"use client";

import { useEffect, useState } from "react";
import axios from "../../plugins/axios";

export default function AuthStatus() {
  const [status, setStatus] = useState("判定中…");

  useEffect(() => {
    axios
      .get("/api/inventory/me/")
      .then(() => setStatus("ログイン中"))
      .catch(() => setStatus("ログアウト"));
  }, []);

  return (
    <div
      style={{
        padding: "8px 12px",
        background: "#eee",
        fontSize: "14px",
        borderBottom: "1px solid #ccc",
      }}
    >
      認証状態：{status}
    </div>
  );
}
