import { Outlet } from "react-router-dom";
import Navbar from "@/components/Navbar";

const Layout = () => {
  return (
    <div className="min-h-screen bg-background">
      {/* Top Navigation */}
      <Navbar />

      {/* Main Content */}
      <main className="pt-16"> 
        {/* Push below navbar height */}
        <div className="max-w-6xl mx-auto px-4">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default Layout;
