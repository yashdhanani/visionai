"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Camera,
  Image as ImageIcon,
  Film,
  FolderOpen,
  Clock,
  BarChart3,
  Cpu,
  Code2,
  Settings,
  Menu,
  X,
  ChevronLeft,
  Search,
  Bell,
  LogOut,
  Sun,
  Moon,
  Crosshair,
  Activity,
} from "lucide-react";
import { useUIStore } from "@/store/ui";
import { useAuthStore } from "@/store/auth";
import { useTheme } from "next-themes";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useState, useEffect } from "react";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/detect", label: "Choose Detection", icon: Crosshair },
  { href: "/live", label: "Live Detection", icon: Camera },
  { href: "/image", label: "Image Detection", icon: ImageIcon },
  { href: "/video", label: "Video Detection", icon: Film },
  { href: "/projects", label: "Projects", icon: FolderOpen },
  { href: "/history", label: "Detection History", icon: Clock },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/diagnostics", label: "Diagnostics", icon: Activity },
  { href: "/models", label: "Models", icon: Cpu },
  { href: "/api-docs", label: "API", icon: Code2 },
  { href: "/settings", label: "Settings", icon: Settings },
];

function Sidebar() {
  const pathname = usePathname();
  const { sidebarOpen, toggleSidebar } = useUIStore();
  const { user, logout } = useAuthStore();
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const router = useRouter();

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <>
      {sidebarOpen && <div className="fixed inset-0 bg-black/20 z-30 lg:hidden" onClick={toggleSidebar} />}
      <aside
        className={cn(
          "fixed left-0 top-0 z-40 h-full bg-card border-r border-border transition-all duration-300 flex flex-col",
          sidebarOpen ? "w-64" : "w-16"
        )}
      >
        <div className="flex items-center h-14 px-4 border-b border-border">
          {sidebarOpen && (
            <Link href="/dashboard" className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-zinc-900 dark:bg-zinc-100 flex items-center justify-center">
                <span className="text-white dark:text-zinc-900 text-xs font-bold">V</span>
              </div>
              <span className="text-lg font-bold tracking-tight">VisionAI</span>
            </Link>
          )}
          <button onClick={toggleSidebar} className="ml-auto p-1 rounded hover:bg-zinc-100 dark:hover:bg-zinc-800">
            {sidebarOpen ? <ChevronLeft className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
          {navItems.map((item) => {
            const active = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                  active ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )}
                title={!sidebarOpen ? item.label : undefined}
              >
                <item.icon className="h-4 w-4 shrink-0" />
                {sidebarOpen && <span>{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        {sidebarOpen && (
          <div className="p-4 border-t border-border">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center text-sm font-medium text-secondary-foreground">
                {user?.name?.charAt(0) || "U"}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{user?.name}</p>
                <p className="text-xs text-zinc-500 truncate">{user?.email}</p>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex gap-1">
                <Button variant="ghost" size="icon" onClick={() => setTheme(theme === "dark" ? "light" : "dark")} title="Toggle theme">
                  {mounted && theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
                </Button>
                <Button variant="ghost" size="icon" onClick={handleLogout} title="Logout">
                  <LogOut className="h-4 w-4" />
                </Button>
              </div>
              <a
                href="https://buymeacoffee.com/dhananiyash"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-[#FFDD00] text-black hover:bg-[#ffea4d] transition-colors shadow-sm"
                title="Support the developer"
              >
                <span>☕</span>
                <span>Coffee</span>
              </a>
            </div>
          </div>
        )}
      </aside>
    </>
  );
}

function TopBar() {
  return (
    <header className="h-14 border-b border-border bg-card flex items-center px-4 gap-4 sticky top-0 z-20">
      <div className="flex-1 max-w-md">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
          <input
            type="search"
            placeholder="Search detections, projects..."
            className="w-full h-9 pl-9 pr-4 rounded-lg border border-border bg-input text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
      </div>
      <Button variant="ghost" size="icon">
        <Bell className="h-4 w-4" />
      </Button>
    </header>
  );
}

export function AppLayout({ children }: { children: React.ReactNode }) {
  const { sidebarOpen } = useUIStore();

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <div className={cn("transition-all duration-300", sidebarOpen ? "ml-64" : "ml-16")}>
        <TopBar />
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}