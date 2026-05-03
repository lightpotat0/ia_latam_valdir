"use client";

import { useState } from "react";
import Image from "next/image";

export default function Home() {
  const [mensagem, setMensagem] = useState("");
  const [chat, setChat] = useState<{ role: string; text: string }[]>([]);
  const [loading, setLoading] = useState(false);

async function enviarMensagem() {
  if (!mensagem) return;
  const texto = mensagem;
  setChat((prev) => [...prev, { role: "user", text: texto }]);
  setMensagem("");
  setLoading(true);
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ pergunta: texto }),
    });

    const data = await res.json();

    setChat((prev) => [
      ...prev,  
      { role: "bot", text: data.resposta },
    ]);
  } catch (err) {
    setChat((prev) => [
      ...prev,
      { role: "bot", text: "Erro ao conectar com a API" },
    ]);
  }
  setLoading(false);
}
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col items-center font-sans">
      <header className="w-full bg-[#1b0088] py-4 flex justify-center shadow-md">
        <Image
          src="/logo_valdir.png"
          alt="LATAM Logo"
          width={180}
          height={60}
          className="object-contain"
        />
      </header>

      <main className="flex-1 w-full max-w-4xl flex flex-col my-6 px-4 md:px-0">
        <div className="flex-1 bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden flex flex-col">
          <div className="flex-1 p-6 overflow-y-auto space-y-4 max-h-[65vh]">
            {chat.length === 0 && (
              <div className="text-center mt-10 text-slate-400">
                <p className="text-xl">Olá! Como a **LATAM** pode te ajudar hoje?</p>
              </div>
            )}
            {chat.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[80%] p-4 rounded-2xl shadow-sm ${
                    msg.role === "user"
                      ? "bg-gray-800 text-white rounded-br-none" 
                      : "bg-[#f3f4f6] text-[#1b0088] rounded-bl-none border border-slate-100"
                  }`}
                >
                  <p className="text-sm leading-relaxed">{msg.text}</p>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start italic text-[#1b0088] text-xs animate-pulse">
                O Valdir está processando sua solicitação...
              </div>
            )}
          </div>
          <div className="p-4 bg-slate-50 border-t border-slate-200 flex gap-3">
            <input
              className="flex-1 p-3 rounded-full border border-slate-300 focus:outline-none focus:ring-2 focus:ring-[#1b0088] transition-all text-slate-800"
              value={mensagem}
              onChange={(e) => setMensagem(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && enviarMensagem()}
              placeholder="Digite sua dúvida sobre voos ou serviços..."
            />
            <button
              onClick={enviarMensagem}
              className="bg-[#1b0088] hover:bg-[#2b1099] text-white px-6 py-2 rounded-full font-bold transition-colors uppercase text-sm tracking-wider"
            >
              Enviar
            </button>
          </div>
        </div>
        <p className="text-center text-[10px] text-slate-400 mt-4 uppercase tracking-widest">
          © 2024 LATAM Airlines - Assistente Virtual Valdir
        </p>
      </main>
    </div>
  );
}