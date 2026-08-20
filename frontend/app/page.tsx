"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import axios from "../plugins/axios";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    axios
      .get("/api/inventory/me/")
      .then(() => {
        router.replace("/inventory/products/");
      })
      .catch(() => {
        router.replace("/login");
      });
  }, [router]);

  return (
    <div className="flex flex-col flex-1 items-center justify-center bg-zinc-50 dark:bg-black">
      <p className="text-zinc-600 dark:text-zinc-400">読み込み中...</p>
    </div>
  );
}