"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Activity, Workflow, Settings, LayoutDashboard } from "lucide-react";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Workflows", href: "/workflows", icon: Workflow },
  { name: "Runs", href: "/runs", icon: Activity },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Header() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center">
        <Link href="/" className="mr-8 flex items-center space-x-2 transition-colors hover:text-foreground/80 cursor-pointer">
          <Activity className="h-6 w-6" />
          <span className="font-bold text-xl">Agentic Platform</span>
        </Link>

        <nav className="flex items-center space-x-6 text-sm font-medium">
          {navigation.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center space-x-2 transition-colors hover:text-foreground/80",
                  pathname.startsWith(item.href) ? "text-foreground" : "text-foreground/60"
                )}
              >
                <Icon className="h-4 w-4" />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>

        <div className="ml-auto flex items-center space-x-4">
          <Link
            href="/workflows/new"
            className="inline-flex h-9 items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90"
          >
            New Workflow
          </Link>
        </div>
      </div>
    </header>
  );
}
