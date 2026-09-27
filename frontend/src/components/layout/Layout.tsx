import { useState } from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout = ({ children }: LayoutProps) => {
  // Sidebar is hidden by default on first visit as requested
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  return (
    <div className="h-screen w-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 flex flex-col overflow-hidden">
      {/* Top Navbar */}
      <Header onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)} />

      {/* Main Content Area + Slide-over Sidebar Drawer */}
      <div className="flex-1 flex min-h-0 relative overflow-hidden">
        <Sidebar isOpen={isSidebarOpen} onToggleSidebar={() => setIsSidebarOpen(false)} />
        <main className="flex-1 flex flex-col min-h-0 w-full overflow-hidden relative">
          {children}
        </main>
      </div>
    </div>
  );
};