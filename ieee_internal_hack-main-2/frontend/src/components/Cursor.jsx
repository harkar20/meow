import { useEffect, useState } from "react";
import { motion } from "framer-motion";

export default function Cursor() {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [isHoveringOptions, setIsHoveringOptions] = useState(false);

  useEffect(() => {
    const updateMousePosition = (e) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
    };

    const handleMouseOver = (e) => {
      // Scale cursor up subtly when hovering over actionable elements
      if (
        e.target.tagName.toLowerCase() === 'button' || 
        e.target.tagName.toLowerCase() === 'a' ||
        e.target.closest('button') || 
        e.target.closest('a') ||
        e.target.tagName.toLowerCase() === 'input'
      ) {
        setIsHoveringOptions(true);
      } else {
        setIsHoveringOptions(false);
      }
    };

    window.addEventListener("mousemove", updateMousePosition);
    window.addEventListener("mouseover", handleMouseOver);

    return () => {
      window.removeEventListener("mousemove", updateMousePosition);
      window.removeEventListener("mouseover", handleMouseOver);
    };
  }, []);

  return (
    <>
      <motion.div
        className="custom-cursor"
        animate={{
          x: mousePosition.x - 16,
          y: mousePosition.y - 16,
          scale: isHoveringOptions ? 1.5 : 1,
          opacity: 1
        }}
        transition={{ type: "tween", ease: "backOut", duration: 0.15 }}
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          width: 32,
          height: 32,
          borderRadius: "50%",
          backgroundColor: isHoveringOptions ? "transparent" : "var(--text-primary)",
          border: isHoveringOptions ? "1.5px solid var(--text-primary)" : "none",
          pointerEvents: "none",
          zIndex: 9999,
          mixBlendMode: "difference", /* Makes it highly sophisticated mathematically inverted across surfaces */
          transform: "translate(-50%, -50%)"
        }}
      />
      <motion.div
        className="custom-cursor-dot"
        animate={{
          x: mousePosition.x - 4,
          y: mousePosition.y - 4,
          opacity: isHoveringOptions ? 0 : 1
        }}
        transition={{ type: "tween", ease: "linear", duration: 0 }}
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          width: 8,
          height: 8,
          borderRadius: "50%",
          backgroundColor: "var(--bg-base)",
          pointerEvents: "none",
          zIndex: 10000,
          mixBlendMode: "difference"
        }}
      />
    </>
  );
}
