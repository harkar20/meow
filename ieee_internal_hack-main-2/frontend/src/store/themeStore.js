import { create } from "zustand";
import { persist } from "zustand/middleware";

export const useThemeStore = create(
  persist(
    (set) => ({
      theme: "light", // 'light', 'dark', 'midnight', 'sepia'
      setTheme: (theme) => set({ theme }),
    }),
    { name: "meowmeow-theme" }
  )
);
