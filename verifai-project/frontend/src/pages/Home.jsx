import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Dropzone from "../components/Dropzone";
import LoadingScreen from "../components/LoadingScreen";
import { analyzeText, analyzeUrl, analyzeUpload } from "../services/api";
import { useAuth } from "../hooks/useAuth";

const TABS  = ["TEXTO", "URL", "IMAGEM"];
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

export default function Home() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [tab,       setTab]       = useState(0);
  const [text,      setText]      = useState("");
  const [url,       setUrl]       = useState("");
  const [imageFile, setImageFile] = useState(null);
  const [loading,   setLoading]   = useState(false);
  const [stage,     setStage]     = useState(0);
  const [error,     setError]     = useState("");

  const canSubmit = () => {
    if (tab === 0) return text.trim().length > 10;
    if (tab === 1) return url.trim().length > 5;
    if (tab === 2) return !!imageFile;
    return false;
  };

  const handleAnalyze = async () => {
    setError(""); setLoading(true); setStage(0);
    try {
      await sleep(700); setStage(1);
      await sleep(700); setStage(2);
      let result;
      if (tab === 0)      result = await analyzeText(text);
      else if (tab === 1) result = await analyzeUrl(url);
      else                result = await analyzeUpload(imageFile);
      setStage(3); await sleep(250);
      sessionStorage.setItem("verifai_result", JSON.stringify(result));
      sessionStorage.setItem("verifai_query",  tab === 0 ? text : tab === 1 ? url : imageFile?.name || "");
      navigate("/report");
    } catch (e) {
      const detail = e?.response?.data?.detail;
      if (detail && typeof detail === "object" && detail.error === "limite_diario") {
        setError(detail.message);
      } else {
        setError(typeof detail === "string" ? detail : e.message || "Erro de conexão com o backend.");
      }
    } finally { setLoading(false); setStage(0); }
  };

  if (loading) return <LoadingScreen stage={stage}/>;

  return (
    <div className="relative min-h-screen overflow-hidden">
      <div className="pointer-events-none fixed inset-0" style={{
        backgroundImage:"linear-gradient(#132435 1px,transparent 1px),linear-gradient(90deg,#132435 1px,transparent 1px)",
        backgroundSize:"48px 48px", opacity:.4 }}/>
      <div className="pointer-events-none fixed left-0 right-0 anim-scanline"
        style={{ height:"8%", background:"linear-gradient(180deg,transparent,rgba(0,212,255,.06),transparent)" }}/>

      <div className="relative z-10 max-w-2xl mx-auto px-5 pt-16 pb-16">
        <div className="flex justify-center mb-6 fade-1">
          <span className="font-mono text-[10px] tracking-[3px] px-4 py-1.5 rounded-full"
            style={{ background:"rgba(0,212,255,.1)", border:"1px solid rgba(0,212,255,.25)", color:"#00D4FF" }}>
            SISTEMA DE AUDITORIA DIGITAL
          </span>
        </div>

        <h1 className="font-syne font-extrabold text-center leading-none mb-4 fade-2"
          style={{ fontSize:"clamp(32px,6vw,58px)" }}>
          <span style={{ color:"#CDE8F0" }}>Detecte </span>
          <span style={{ background:"linear-gradient(135deg,#00D4FF,#00FF87)", WebkitBackgroundClip:"text", WebkitTextFillColor:"transparent" }}>
            desinformacao
          </span>
          <br/><span style={{ color:"#CDE8F0" }}>em tempo real.</span>
        </h1>

        <p className="text-center font-mono text-[11px] leading-relaxed mb-10 fade-3" style={{ color:"#3A6070" }}>
          Ola, {user?.name?.split(" ")[0]}! 3 camadas de verificacao: agencias · dominio · Gemini 2.5 Flash.
        </p>

        <div className="rounded-2xl overflow-hidden fade-4" style={{
          background:"#0A1520", border:"1px solid #132435",
          boxShadow:"0 40px 80px rgba(0,0,0,.5), 0 0 0 1px rgba(0,212,255,.04)" }}>

          <div className="flex border-b" style={{ borderColor:"#132435", padding:"0 20px" }}>
            {TABS.map((t,i) => (
              <button key={t} onClick={() => setTab(i)}
                className="font-mono text-[10px] tracking-[2px] px-5 py-3.5 transition-all"
                style={{
                  color: tab===i?"#00D4FF":"#1A3A50",
                  borderBottom: tab===i?"2px solid #00D4FF":"2px solid transparent",
                  marginBottom:-1, background:"transparent", cursor:"pointer" }}>
                {t}
              </button>
            ))}
          </div>

          <div className="p-5">
            {tab===0&&<div className="relative">
              <textarea value={text} onChange={e=>setText(e.target.value)}
                placeholder="Cole aqui um texto, link ou manchete suspeita para analise forense..." rows={6}
                className="w-full font-mono text-[13px] leading-relaxed resize-none"
                style={{ background:"transparent", border:"none", color:"#CDE8F0", letterSpacing:.3 }}/>
              <span className="absolute bottom-1 right-2 font-mono text-[10px]"
                style={{ color:text.length>4500?"#FFB830":"#1A3A50" }}>{text.length}/5000</span>
            </div>}
            {tab===1&&<input type="url" value={url} onChange={e=>setUrl(e.target.value)}
              placeholder="https://exemplo.com/noticia-suspeita"
              className="w-full font-mono text-[13px] py-4"
              style={{ background:"transparent", border:"none", color:"#CDE8F0" }}/>}
            {tab===2&&<Dropzone onFile={setImageFile}/>}
          </div>

          <div className="flex items-center justify-between px-5 py-3.5 border-t"
            style={{ borderColor:"#132435", background:"#0F1E2E" }}>
            <div className="flex gap-3">
              {[["Camada 1","#00D4FF"],["Camada 2","#00FF87"],["Camada 3","#FFB830"]].map(([lbl,col])=>(
                <span key={lbl} className="flex items-center gap-1.5 font-mono text-[9px]" style={{ color:"#3A6070" }}>
                  <span className="w-1.5 h-1.5 rounded-full" style={{ background:col }}/>
                  {lbl}
                </span>
              ))}
            </div>
            <button disabled={!canSubmit()} onClick={handleAnalyze}
              className="font-syne font-bold text-[12px] tracking-widest px-7 py-2.5 rounded-lg transition-all"
              style={{
                background: canSubmit()?"linear-gradient(135deg,#00D4FF,#00FF87)":"#1A3A50",
                color: canSubmit()?"#04080C":"#3A6070",
                border:"none", cursor:canSubmit()?"pointer":"not-allowed",
                boxShadow: canSubmit()?"0 0 24px rgba(0,212,255,.35)":"none" }}>
              ANALISAR
            </button>
          </div>
        </div>

        {error&&(
          <div className="mt-4 px-4 py-3 rounded-lg font-mono text-[11px] fade-1"
            style={{ background:"rgba(255,59,92,.1)", border:"1px solid rgba(255,59,92,.3)", color:"#FF3B5C" }}>
            {error}
            {error.includes("Limite") && (
              <button onClick={() => navigate("/plans")}
                className="ml-3 underline font-mono text-[11px]" style={{ color:"#00D4FF", cursor:"pointer", background:"none", border:"none" }}>
                Ver planos
              </button>
            )}
          </div>
        )}

        <div className="flex justify-center gap-8 mt-8 fade-5">
          {[["Fact Check API","#00D4FF"],["XAI Explicavel","#00D4FF"],["Gemini 2.5","#00D4FF"]].map(([lbl,col])=>(
            <span key={lbl} className="font-mono text-[11px]" style={{ color:"#3A6070" }}>
              <span style={{ color:col }}>*</span> {lbl}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
