"use client";

import { useEffect, useRef, useState } from "react";
import { uploadImage } from "../../lib/api";

export interface PickedImage {
  id: string;
  previewUrl: string;
  name: string;
}

interface Props {
  image: PickedImage | null;
  disabled: boolean;
  onChange: (img: PickedImage | null) => void;
  onError: (msg: string) => void;
}

/** Chọn ảnh đề bài: bấm nút, kéo-thả, hoặc dán từ clipboard (Ctrl+V). */
export function ImagePicker({ image, disabled, onChange, onError }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [dragging, setDragging] = useState(false);

  async function accept(file: File | null | undefined) {
    if (!file || disabled) return;
    if (!file.type.startsWith("image/")) {
      onError("Chỉ nhận ảnh PNG, JPG hoặc WEBP.");
      return;
    }
    setBusy(true);
    try {
      const { image_id } = await uploadImage(file);
      onChange({ id: image_id, previewUrl: URL.createObjectURL(file), name: file.name || "ảnh đã dán" });
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  // Dán ảnh từ clipboard — cách nhanh nhất khi chụp màn hình đề
  useEffect(() => {
    function onPaste(e: ClipboardEvent) {
      const file = Array.from(e.clipboardData?.items ?? [])
        .find((i) => i.type.startsWith("image/"))
        ?.getAsFile();
      if (file) {
        e.preventDefault();
        void accept(file);
      }
    }
    window.addEventListener("paste", onPaste);
    return () => window.removeEventListener("paste", onPaste);
  });

  useEffect(() => () => {
    if (image) URL.revokeObjectURL(image.previewUrl);
  }, [image]);

  if (image) {
    return (
      <div className="pick pick--has">
        <img src={image.previewUrl} alt="Ảnh đề bài" />
        <div>
          <div><b>📸 {image.name}</b></div>
          <div className="muted">Đề trong ảnh sẽ được đọc trước khi giải.</div>
          <button type="button" className="linkbtn" onClick={() => onChange(null)} disabled={disabled}>
            Bỏ ảnh
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`pick${dragging ? " pick--drag" : ""}`}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => { e.preventDefault(); setDragging(false); void accept(e.dataTransfer.files?.[0]); }}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp"
        hidden
        onChange={(e) => { void accept(e.target.files?.[0]); e.target.value = ""; }}
      />
      <span className="pick__icon" aria-hidden>📷</span>
      <button type="button" className="btn btn--ghost" onClick={() => inputRef.current?.click()} disabled={disabled || busy}>
        {busy ? "Đang tải ảnh..." : "Chụp / chọn ảnh đề"}
      </button>
      <span className="muted">hoặc kéo ảnh vào đây, hoặc dán bằng Ctrl+V</span>
    </div>
  );
}
