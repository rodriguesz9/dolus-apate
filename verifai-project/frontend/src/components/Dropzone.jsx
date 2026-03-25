import { useRef, useState } from "react";

export default function Dropzone({ onFile }) {
  const inputRef  = useRef(null);
  const [drag, setDrag]       = useState(false);
  const [preview, setPreview] = useState(null);
  const [fileName, setFileName] = useState("");

  const accept = "image/jpeg,image/png,image/webp,image/gif";

  const handleFile = (file) => {
    if (!file) return;
    setFileName(file.name);
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target.result);
    reader.readAsDataURL(file);
    onFile(file);
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDrag(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  };

  return (
    <div
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
      onDragLeave={() => setDrag(false)}
      onDrop={onDrop}
      className="rounded-xl border transition-all cursor-pointer flex flex-col items-center justify-center gap-3 p-8 relative overflow-hidden"
      style={{
        borderColor:  drag ? "#00D4FF" : "#132435",
        borderStyle:  "dashed",
        background:   drag ? "rgba(0,212,255,.06)" : "#0A1520",
        minHeight:    160,
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => handleFile(e.target.files[0])}
      />

      {preview ? (
        <img
          src={preview}
          alt="preview"
          className="max-h-32 rounded-lg object-contain opacity-80"
        />
      ) : (
        <div className="flex flex-col items-center gap-2">
          <span className="text-3xl" style={{ color: "#1A3A50" }}>⬡</span>
          <span className="font-mono text-[11px] tracking-widest text-muted">
            ARRASTE OU CLIQUE PARA ENVIAR
          </span>
          <span className="font-mono text-[10px]" style={{ color: "#1A3A50" }}>
            JPEG · PNG · WebP · GIF · máx 8 MB
          </span>
        </div>
      )}

      {fileName && (
        <span className="font-mono text-[10px] text-cyan mt-1">{fileName}</span>
      )}
    </div>
  );
}
