import { Link } from "react-router-dom";

const NotFound = () => {
  return (
    <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center bg-background px-4">
      <div className="text-center animate-fadeIn">
        <div className="text-6xl mb-4">🌾</div>

        <h1 className="mb-2 text-5xl font-bold text-foreground">404</h1>
        <p className="mb-6 text-lg text-muted-foreground">
          Oops! The page you're looking for doesn't exist.
        </p>

        <Link
          to="/"
          className="text-primary font-medium underline hover:text-primary/80 transition-colors"
        >
          Go back to Home
        </Link>
      </div>
    </div>
  );
};

export default NotFound;
