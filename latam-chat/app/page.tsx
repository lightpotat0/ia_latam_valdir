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
    const res = await fetch("https://ialatamvaldir-production.up.railway.app/chat", {
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
      <div className="min-h-screen bg-gray-50 text-white flex flex-col items-center">
        <Image
            src="/valdir_logo-.png"
            alt="Valdir"
            width={300}
            height={120}
            className="mt-6 border-5 border-b-blue-700"
        />
        <div className="min-h-200 bg-blue-400 text-white flex flex-col w-250 ml-auto mr-110 border-4 border-blue-500 rounded-2xl shadow-lg">

          <div className="flex-1 p-20 overflow-y-auto w-1200px h-auto m-5 bg-blue-950">
            {chat.map((msg, i) => (
                <div
                    key={i}
                    className={`mb-3 ${
                        msg.role === "user" ? "text-right" : "text-left"
                    }`}
                >
                  <div
                      className={`inline-block p-3 rounded-xl max-w-[70%] ${
                          msg.role === "user"
                              ? "bg-blue-500"
                              : "bg-gray-700"
                      }`}
                  >
                    {msg.text}
                  </div>
                </div>
            ))}

            {loading && <p className="text-gray-400">Pensando...</p>}
          </div>

          <div className="p-4 flex gap-2 border-t border-gray-700">
            <input
                className="flex-1 p-2 rounded bg-gray-800"
                value={mensagem}
                onChange={(e) => setMensagem(e.target.value)}
                placeholder="Pergunte algo..."
            />
            <button
                onClick={enviarMensagem}
                className="bg-blue-600 px-4 rounded"
            >
              Enviar
            </button>
          </div>

        </div>
      </div>
  );
}