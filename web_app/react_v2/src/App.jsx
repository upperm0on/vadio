import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Zap, Shield, Volume2, Radio } from 'lucide-react';
import './App.css';

const VIBES = {
  "Cinematic Aura": { color: "#FF3333", rgb: "255,51,51", icon: Zap, label: "ASCENSION" },
  "Mental Agony": { color: "#AA33FF", rgb: "170,51,255", icon: Activity, label: "COLLAPSE" },
  "True Warrior": { color: "#33AAFF", rgb: "51,170,255", icon: Shield, label: "STOICISM" }
};

const App = () => {
  const [activeVibe, setActiveVibe] = useState(null);
  const [currentTrack, setCurrentTrack] = useState({ title: 'AWAITING LINK', uploader: 'UNKNOWN SOURCE' });
  const [status, setStatus] = useState('SYSTEM IDLE');
  const [playbackRate, setPlaybackRate] = useState(1.0);
  
  const playerA = useRef(null);
  const playerB = useRef(null);
  const audioCtx = useRef(null);
  const analyser = useRef(null);
  const gainNodes = useRef({ A: null, B: null });
  const currentPlayer = useRef('A');
  const vibeCache = useRef({});
  const isTransitioning = useRef(false);

  // --- Audio Context Init ---
  const initAudio = () => {
    if (!audioCtx.current) {
      audioCtx.current = new (window.AudioContext || window.webkitAudioContext)();
      analyser.current = audioCtx.current.createAnalyser();
      analyser.current.fftSize = 128;
      
      gainNodes.current.A = audioCtx.current.createGain();
      gainNodes.current.B = audioCtx.current.createGain();
      
      const sA = audioCtx.current.createMediaElementSource(playerA.current);
      const sB = audioCtx.current.createMediaElementSource(playerB.current);
      
      sA.connect(gainNodes.current.A);
      sB.connect(gainNodes.current.B);
      
      gainNodes.current.A.connect(analyser.current);
      gainNodes.current.B.connect(analyser.current);
      analyser.current.connect(audioCtx.current.destination);
      
      gainNodes.current.A.gain.value = 1;
      gainNodes.current.B.gain.value = 0;
    }
    if (audioCtx.current.state === 'suspended') audioCtx.current.resume();
  };

  const fetchTrack = async (vibe) => {
    try {
      const res = await fetch('http://localhost:8090/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vibe })
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      return data;
    } catch (e) {
      console.error("Fetch failed", e);
      return null;
    }
  };

  const refillCache = async (vibe) => {
    const data = await fetchTrack(vibe);
    if (data) {
      vibeCache.current[vibe] = data;
      if (vibe === activeVibe) {
        const nextP = currentPlayer.current === 'A' ? playerB.current : playerA.current;
        nextP.src = `${data.url}?t=${Date.now()}`;
        nextP.load();
      }
    }
  };

  const handleCrossfade = async () => {
    if (isTransitioning.current || !activeVibe) return;
    
    const nextData = vibeCache.current[activeVibe];
    if (!nextData) {
      refillCache(activeVibe);
      return;
    }

    isTransitioning.current = true;
    const fadeTime = 3;
    const now = audioCtx.current.currentTime;
    
    const outgoingPlayer = currentPlayer.current === 'A' ? playerA.current : playerB.current;
    const incomingPlayer = currentPlayer.current === 'A' ? playerB.current : playerA.current;
    const outgoingGain = currentPlayer.current === 'A' ? gainNodes.current.A : gainNodes.current.B;
    const incomingGain = currentPlayer.current === 'A' ? gainNodes.current.B : gainNodes.current.A;

    const rate = 0.98 + (Math.random() * 0.04);
    setPlaybackRate(rate);
    incomingPlayer.playbackRate = rate;
    
    // We update UI to show the next track metadata as it fades in
    setCurrentTrack(nextData.metadata);
    setStatus(`TRANSITION: ${VIBES[activeVibe].label}`);

    try {
        await incomingPlayer.play();
    } catch (e) {
        console.warn("Playback prevented", e);
        isTransitioning.current = false;
        return;
    }

    outgoingGain.gain.setValueAtTime(outgoingGain.gain.value, now);
    outgoingGain.gain.linearRampToValueAtTime(0, now + fadeTime);
    
    incomingGain.gain.setValueAtTime(0, now);
    incomingGain.gain.linearRampToValueAtTime(1, now + fadeTime);

    setTimeout(() => {
      outgoingPlayer.pause();
      currentPlayer.current = currentPlayer.current === 'A' ? 'B' : 'A';
      isTransitioning.current = false;
      refillCache(activeVibe);
    }, fadeTime * 1000);
  };

  const handleVibeClick = async (vibe) => {
    initAudio();
    setActiveVibe(vibe);
    setStatus(`LINKING ${vibe.toUpperCase()}...`);
    
    const track = vibeCache.current[vibe] || await fetchTrack(vibe);
    if (track) {
      const p = currentPlayer.current === 'A' ? playerA.current : playerB.current;
      const g = currentPlayer.current === 'A' ? gainNodes.current.A : gainNodes.current.B;
      
      const rate = 0.98 + (Math.random() * 0.04);
      setPlaybackRate(rate);
      
      p.src = `${track.url}?t=${Date.now()}`;
      p.playbackRate = rate;
      g.gain.value = 1; // Ensure current player is audible
      
      try {
          await p.play();
          setCurrentTrack(track.metadata);
          setStatus(`CONNECTED: ${VIBES[vibe].label}`);
          refillCache(vibe);
      } catch (e) {
          setStatus("CLICK TO START AUDIO");
      }
    }
  };

  // Monitor for transitions
  useEffect(() => {
    const pA = playerA.current;
    const pB = playerB.current;
    
    const check = () => {
        const p = currentPlayer.current === 'A' ? pA : pB;
        if (p && p.duration && p.currentTime > p.duration - 5 && !isTransitioning.current) {
            handleCrossfade();
        }
        requestAnimationFrame(check);
    };
    
    const animId = requestAnimationFrame(check);
    return () => cancelAnimationFrame(animId);
  }, [activeVibe]);

  return (
    <div className="void-container" style={{ "--theme": activeVibe ? VIBES[activeVibe].color : "#555" }}>
      <Visualizer analyser={analyser.current} activeVibe={activeVibe} />
      
      <main className="ui-wrapper">
        <header className="navbar">
          <div className="logo"><Radio size={18} /> VOID<span>ENGINE</span></div>
          <div className="version">R2.2026</div>
        </header>

        <section className="track-display">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            key={currentTrack.title}
            className="metadata"
          >
            <div 
              className="status-badge" 
              onClick={() => {
                const p = currentPlayer.current === 'A' ? playerA.current : playerB.current;
                p.play().catch(e => console.error("Force play failed:", e));
                if (audioCtx.current && audioCtx.current.state === 'suspended') {
                  audioCtx.current.resume();
                }
                setStatus(`CONNECTED: ${VIBES[activeVibe]?.label || 'AURA'}`);
              }}
              style={{ cursor: 'pointer' }}
            >
              <span className="dot" /> {status}
            </div>
            <h1 className="title">{currentTrack.title}</h1>
            <p className="uploader">SOURCE: {currentTrack.uploader}</p>
          </motion.div>
        </section>

        <footer className="vibe-grid">
          {Object.entries(VIBES).map(([name, data]) => (
            <button 
              key={name}
              onClick={() => handleVibeClick(name)}
              className={`vibe-btn ${activeVibe === name ? 'active' : ''}`}
            >
              <data.icon size={20} />
              <div className="btn-meta">
                <span className="vibe-name">{name}</span>
                <span className="vibe-label">{data.label}</span>
              </div>
            </button>
          ))}
        </footer>
      </main>

      <audio ref={playerA} crossOrigin="anonymous" />
      <audio ref={playerB} crossOrigin="anonymous" />
    </div>
  );
};

const Visualizer = ({ analyser, activeVibe }) => {
  const canvasRef = useRef(null);
  
  useEffect(() => {
    if (!analyser || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const render = () => {
      requestAnimationFrame(render);
      analyser.getByteFrequencyData(dataArray);
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      const barWidth = (canvas.width / bufferLength) * 2.5;
      let x = 0;
      const rgb = activeVibe ? VIBES[activeVibe].rgb : "85,85,85";

      for (let i = 0; i < bufferLength; i++) {
        const barHeight = dataArray[i] * 2;
        ctx.fillStyle = `rgba(${rgb}, ${dataArray[i]/255})`;
        ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
        x += barWidth + 1;
      }
    };
    render();
  }, [analyser, activeVibe]);

  return <canvas ref={canvasRef} className="void-canvas" />;
};

export default App;
