import { Link, useLocation } from "react-router-dom";
import { Sprout, MessageSquare, Image, History } from "lucide-react";
import { cn } from "@/lib/utils";

const Navbar = () => {
  const location = useLocation();

  const navItems = [
    { path: "/", label: "Chat", icon: MessageSquare },
    { path: "/image", label: "Image Diagnosis", icon: Image },
    { path: "/history", label: "History", icon: History },
  ];

  const isActivePath = (path: string) => location.pathname === path;

  return (
    <nav className="bg-card border-b border-border sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">

        {/* Logo */}
        <Link to="/" className="flex items-center space-x-3 group">
          <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform">
            <Sprout className="w-6 h-6 text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-foreground leading-tight">AgriGPT</h1>
            <p className="text-xs text-muted-foreground">Your Farming Assistant</p>
          </div>
        </Link>

        {/* Desktop Navigation */}
        <div className="hidden md:flex items-center space-x-2">
          {navItems.map(({ path, label, icon: Icon }) => (
            <Link
              key={path}
              to={path}
              className={cn(
                "flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors",
                isActivePath(path)
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-foreground hover:bg-secondary"
              )}
            >
              <Icon className="w-4 h-4" />
              <span className="text-sm font-medium">{label}</span>
            </Link>
          ))}
        </div>

        {/* Mobile Navigation */}
        <div className="flex md:hidden items-center space-x-2">
          {navItems.map(({ path, icon: Icon }) => (
            <Link
              key={path}
              to={path}
              aria-label={path}
              className={cn(
                "p-2 rounded-lg transition-colors",
                isActivePath(path)
                  ? "bg-primary text-primary-foreground"
                  : "text-foreground hover:bg-secondary"
              )}
            >
              <Icon className="w-5 h-5" />
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
