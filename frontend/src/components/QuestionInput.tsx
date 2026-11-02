import { useRef } from "react";
import { ArrowUp } from "lucide-react";

interface QuestionInputProps {
    value: string;
    onChange: (value: string) => void;
    onSubmit: () => void;
    disabled?: boolean;
    placeholder?: string;
    autoFocus?: boolean;
}

export default function QuestionInput({
    value,
    onChange,
    onSubmit,
    disabled = false,
    placeholder = "Ask your research question...",
    autoFocus = false,
}: QuestionInputProps) {
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            if (value.trim() && !disabled) onSubmit();
        }
    };

    const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        onChange(e.target.value);
        const el = textareaRef.current;
        if (el) {
            el.style.height = "auto";
            el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
        }
    };

    return (
        <div className="flex items-end gap-2 rounded-2xl border border-border bg-white px-3.5 py-2.5 shadow-card transition-colors focus-within:border-accent/50">
            <textarea
                ref={textareaRef}
                value={value}
                onChange={handleInput}
                onKeyDown={handleKeyDown}
                placeholder={placeholder}
                disabled={disabled}
                autoFocus={autoFocus}
                rows={1}
                className="max-h-40 flex-1 resize-none bg-transparent text-[15px] leading-6 text-ink placeholder:text-ink-faint focus:outline-none disabled:opacity-60"
            />
            <button
                onClick={onSubmit}
                disabled={disabled || !value.trim()}
                aria-label="Submit question"
                className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-ink text-white transition-all hover:bg-ink/85 disabled:cursor-not-allowed disabled:bg-border disabled:text-ink-faint"
            >
                <ArrowUp size={16} strokeWidth={2.5} />
            </button>
        </div>
    );
}
