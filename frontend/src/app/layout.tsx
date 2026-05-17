import type { Metadata } from 'next';
import { Geist, Geist_Mono } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/context/AuthContext';
import ChatSidebar from '@/components/ChatSidebar';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  title: 'Flight Chatbot',
  description: 'Hệ thống Chatbot Tìm kiếm vé máy bay',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <AuthProvider>
          <div className="flex h-screen w-full bg-gray-100 overflow-hidden">
            <div className="flex shrink-0">
              <ChatSidebar />
            </div>

            <main className="h-full w-full flex-1 overflow-hidden">{children}</main>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
