"use client";

export function OpenChatButton({ className }: { className?: string }) {
  function handleClick() {
    const btn = document.querySelector<HTMLButtonElement>("[data-chat-trigger]");
    btn?.click();
  }

  return (
    <button onClick={handleClick} className={className}>
      AI bilan suhbatlash
    </button>
  );
}
