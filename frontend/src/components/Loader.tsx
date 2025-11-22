import { Loader2, Sprout } from "lucide-react";

interface LoaderProps {
  message?: string;
}

const Loader = ({ message = "Processing your request..." }: LoaderProps) => {
  return (
    <div
      role="status"
      aria-live="polite"
      className="flex flex-col items-center justify-center py-8 space-y-4 animate-fadeIn"
    >
      <div className="relative flex items-center justify-center">
        <Loader2 className="w-12 h-12 text-primary animate-spin" />
        <Sprout
          className="w-6 h-6 text-accent absolute inset-0 m-auto animate-bounce-slow"
        />
      </div>

      <p className="text-sm text-muted-foreground animate-pulse">
        {message}
      </p>
    </div>
  );
};

export default Loader;
