import React, { useState, useRef, useEffect } from "react";
import { 
  BotIcon, 
  UserIcon, 
  SendIcon, 
  LoaderIcon, 
  SunIcon, 
  MoonIcon, 
  TrashIcon,
  PlusIcon,
  MessageSquareIcon,
  MenuIcon,
  SquareIcon
} from "../icons";

const TypewriterText = ({ text, delay = 15, onComplete, onUpdate, isStopped }) => {
  const [currentText, setCurrentText] = useState("");
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (isStopped) return;

    if (currentIndex < text.length) {
      const timeout = setTimeout(() => {
        const nextText = currentText + text[currentIndex];
        setCurrentText(nextText);
        setCurrentIndex((prev) => prev + 1);
        if (onUpdate) onUpdate(nextText);
      }, delay);
      return () => clearTimeout(timeout);
    } else if (onComplete) {
      onComplete();
    }
  }, [currentIndex, delay, text, onComplete, onUpdate, isStopped, currentText]);

  return <p className="whitespace-pre-wrap">{currentText}</p>;
};

const SourcesPanel = ({ sources }) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-3 border-t border-zinc-200 dark:border-zinc-700/50 pt-3">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1.5 text-xs font-medium text-zinc-500 hover:text-zinc-800 dark:text-zinc-400 dark:hover:text-zinc-200 transition-colors"
        aria-expanded={isOpen}
      >
        <span>{isOpen ? 'Hide Sources' : 'Show Sources'}</span>
        <svg
          className={`h-3 w-3 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="m6 9 6 6 6-6"/>
        </svg>
      </button>
      
      {isOpen && (
        <div className="mt-2.5 flex flex-col gap-2">
          {sources.map((source, idx) => (
            <div key={idx} className="flex flex-col gap-1 rounded-md border border-zinc-200 dark:border-zinc-700/50 bg-white/50 dark:bg-zinc-800/50 p-2.5">
              <div className="flex items-center gap-2">
                <span className="font-mono text-[10px] bg-zinc-100 dark:bg-zinc-900 px-1.5 py-0.5 rounded text-zinc-600 dark:text-zinc-400">
                  {source.commit_id ? source.commit_id.substring(0, 7) : 'commit'}
                </span>
                <span className="text-xs font-medium font-mono text-blue-600 dark:text-blue-400 truncate">
                  {source.file_name || source.filename}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export function ChatApp() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: "assistant",
      content: "Hello! I'm ready to help. What would you like to discuss today?",
      isNew: false,
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false); // Mobile sidebar state
  const [abortController, setAbortController] = useState(null);
  const [isAnimating, setIsAnimating] = useState(false);
  const [isStopped, setIsStopped] = useState(false);
  
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const partialContentRef = useRef("");

  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [isDarkMode]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        200
      )}px`;
    }
  }, [inputValue]);

  const handleClearChat = () => {
    // Optionally close sidebar on mobile when navigating
    setIsSidebarOpen(false);
    
    // We mock clear chat visually instead of prompt for a pure layout feel
    setMessages([
      {
        id: Date.now(),
        role: "assistant",
        content: "Started a new conversation. How can I assist?",
        isNew: true,
      },
    ]);
  };

  const handleSend = async () => {
    if (!inputValue.trim() || isTyping || isAnimating) return;

    const query = inputValue.trim();
    setIsStopped(false);
    partialContentRef.current = "";
    const newUserMessage = {
      id: Date.now(),
      role: "user",
      content: query,
      isNew: false,
    };

    setMessages((prev) => [
      ...prev.map(m => ({ ...m, isNew: false })), 
      newUserMessage
    ]);
    setInputValue("");
    setIsTyping(true);

    const controller = new AbortController();
    setAbortController(controller);

    const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
    
    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        signal: controller.signal,
        body: JSON.stringify({ query }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      const newAssistantMessage = {
        id: Date.now() + 1,
        role: "assistant",
        content: data.answer || "Sorry, I received an empty response.",
        sources: data.sources || [],
        isNew: true,
      };
      setMessages((prev) => [
        ...prev.map(m => ({ ...m, isNew: false })), 
        newAssistantMessage
      ]);
      setIsAnimating(true);
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('Fetch aborted');
      } else {
        console.error("Error fetching chat response:", error);
        const errorMessage = {
          id: Date.now() + 1,
          role: "assistant",
          content: "Sorry, I encountered an error connecting to the server. Please try again.",
          isNew: true,
        };
        setMessages((prev) => [...prev, errorMessage]);
      }
    } finally {
      setIsTyping(false);
      setAbortController(null);
    }
  };

  const handleStop = () => {
    if (abortController) {
      abortController.abort();
    }
    
    // Truncate the message content to where it was stopped
    setMessages(prev => {
      const newMessages = [...prev];
      const lastMsg = newMessages[newMessages.length - 1];
      if (lastMsg && lastMsg.role === "assistant") {
        lastMsg.content = partialContentRef.current;
        lastMsg.isNew = false;
      }
      return newMessages;
    });

    setIsStopped(true);
    setIsTyping(false);
    setIsAnimating(false);
    setAbortController(null);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Mock chat history
  const mockHistory = [
    { id: '1', title: "Reviewing PCB layout" },
    { id: '2', title: "Routing impedance check" },
    { id: '3', title: "Fix DRC errors" },
  ];

  return (
    <div className="flex h-screen w-full overflow-hidden bg-white dark:bg-zinc-900 font-sans">
      
      {/* Mobile Sidebar Overlay */}
      {isSidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/60 z-40 md:hidden transition-opacity"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Sidebar (Always Dark) */}
      <aside 
        className={`fixed md:static inset-y-0 left-0 z-50 w-[260px] flex-shrink-0 flex flex-col bg-zinc-950 text-zinc-300 transition-transform duration-300 ease-in-out ${
          isSidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        }`}
      >
        <div className="flex items-center justify-between p-4 px-5 relative h-[60px]">
          <h1 className="font-semibold text-[17px] tracking-tight text-zinc-100 flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-md bg-blue-600 text-white">
              <BotIcon className="h-4 w-4" />
            </span>
            FluxLink
          </h1>
          {/* Mobile close button */}
          <button 
            className="md:hidden p-1 text-zinc-400 hover:text-white"
            onClick={() => setIsSidebarOpen(false)}
          >
            <PlusIcon className="h-5 w-5 rotate-45" />
          </button>
        </div>
        
        <div className="px-3 pb-3 pt-2">
          <button 
            onClick={handleClearChat}
            className="w-full flex items-center justify-start gap-3 bg-white/5 hover:bg-white/10 px-3 py-2.5 rounded-lg text-sm font-medium text-zinc-100 transition-all active:scale-[0.98]"
          >
            <PlusIcon className="h-4 w-4" />
            New Chat
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto px-3 py-2">
          {/* History List */}
          <p className="text-xs font-semibold text-zinc-500 mb-2 mt-4 px-2 tracking-wide">
            Today
          </p>
          <div className="space-y-0.5">
            <button className="w-full text-left flex items-center gap-3 px-3 py-2.5 rounded-lg bg-zinc-800 text-sm font-medium text-zinc-200">
              <MessageSquareIcon className="h-4 w-4 shrink-0 text-zinc-400" />
              <span className="truncate">Current Conversation</span>
            </button>
          </div>

          <p className="text-xs font-semibold text-zinc-500 mb-2 mt-6 px-2 tracking-wide">
            Previous 7 Days
          </p>
          <div className="space-y-0.5">
            {mockHistory.map((item) => (
              <button 
                key={item.id}
                className="w-full text-left flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-white/5 text-sm text-zinc-400 hover:text-zinc-200 transition-colors"
                title={item.title}
              >
                <MessageSquareIcon className="h-4 w-4 shrink-0 opacity-50" />
                <span className="truncate">{item.title}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Sidebar Footer */}
        <div className="p-3 mt-auto border-t border-white/10">
          <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-white/5 text-sm text-zinc-400 hover:text-zinc-200 transition-colors">
            <UserIcon className="h-4 w-4" />
            User Settings
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col relative w-full h-full min-w-0 min-h-0 overflow-hidden bg-white dark:bg-zinc-900 transition-colors duration-300">
        
        {/* Top Header Row for Mobile Toggle & Theme Utilities */}
        <header className="shrink-0 z-20 flex h-[60px] items-center justify-between px-4 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-md border-b border-zinc-200/50 dark:border-zinc-800/50">
          <div className="flex items-center">
            {/* Mobile Sidebar Toggle Button */}
            <button 
              className="md:hidden flex h-9 w-9 items-center justify-center rounded-md text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800 mr-2"
              onClick={() => setIsSidebarOpen(true)}
              aria-label="Open sidebar"
            >
              <MenuIcon className="h-5 w-5" />
            </button>
            <h2 className="md:hidden font-medium text-zinc-800 dark:text-zinc-200 text-sm">
              FluxLink
            </h2>
          </div>
          
          <div className="flex flex-1 justify-end items-center gap-2">
            <button
               onClick={() => setIsDarkMode(!isDarkMode)}
               className="flex h-9 w-9 items-center justify-center rounded-full text-zinc-500 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800 transition-colors"
               aria-label="Toggle dark mode"
               title="Toggle theme"
             >
               {isDarkMode ? <SunIcon className="h-4 w-4" /> : <MoonIcon className="h-4 w-4" />}
             </button>
          </div>
        </header>

        {/* Scrollable Chat Message List */}
        <main className="flex-1 min-h-0 overflow-y-auto w-full scroll-smooth">
          <div className="mx-auto w-full max-w-3xl p-3 sm:p-6 space-y-6 sm:space-y-8">
            
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full pt-20 pb-10">
                <div className="h-16 w-16 bg-zinc-100 dark:bg-zinc-800 rounded-full flex items-center justify-center mb-4">
                  <BotIcon className="h-8 w-8 text-black dark:text-white opacity-50" />
                </div>
                <h3 className="text-xl font-medium text-zinc-800 dark:text-zinc-200 mb-2">How can I help you today?</h3>
              </div>
            )}

            {messages.map((message) => (
              <div
                key={message.id}
                className="flex w-full group animate-in fade-in slide-in-from-bottom-2 duration-500 justify-start"
              >
                <div className="flex w-full max-w-3xl gap-4 md:gap-6">
                  {/* Avatar Fixed on Left */}
                  <div
                    className={`flex h-7 w-7 sm:h-8 sm:w-8 shrink-0 items-center justify-center rounded-sm shadow-sm ring-1 ring-black/5 dark:ring-white/10 ${
                      message.role === "user"
                        ? "bg-white text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300"
                        : "bg-blue-600 text-white"
                    }`}
                  >
                    {message.role === "user" ? <UserIcon className="h-4 w-4 sm:h-5 sm:w-5" /> : <BotIcon className="h-4 w-4 sm:h-5 sm:w-5" />}
                  </div>

                  {/* Message Content Area */}
                  <div className="flex flex-col gap-1.5 min-w-0 w-full pt-0.5">
                    <div className="text-sm font-semibold text-zinc-800 dark:text-zinc-200 flex items-center gap-2">
                      {message.role === "user" ? "You" : "Assistant"}
                    </div>
                    <div className="text-[15px] leading-relaxed text-zinc-800 dark:text-zinc-200 prose prose-zinc dark:prose-invert max-w-none">
                      {message.role === "assistant" && message.isNew ? (
                        <TypewriterText 
                          text={message.content} 
                          onComplete={() => setIsAnimating(false)}
                          onUpdate={(val) => partialContentRef.current = val}
                          isStopped={isStopped}
                        />
                      ) : (
                        <p className="whitespace-pre-wrap">{message.content}</p>
                      )}
                      
                      {message.role === "assistant" && (
                        <SourcesPanel sources={message.sources} />
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}

            {/* Typing Indicator */}
            {isTyping && (
              <div className="flex w-full group animate-in fade-in duration-300 justify-start">
                <div className="flex w-full max-w-3xl gap-4 md:gap-6">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-sm bg-blue-600 text-white shadow-sm ring-1 ring-black/5 dark:ring-white/10">
                    <BotIcon className="h-5 w-5" />
                  </div>
                  <div className="flex flex-col gap-1.5 pt-0.5">
                    <div className="text-sm font-semibold text-zinc-800 dark:text-zinc-200">
                      Assistant
                    </div>
                    <div className="flex items-center gap-2 pt-2">
                       <span className="h-2 w-2 rounded-full bg-zinc-300 dark:bg-zinc-600 animate-bounce" style={{ animationDelay: '0ms' }} />
                       <span className="h-2 w-2 rounded-full bg-zinc-300 dark:bg-zinc-600 animate-bounce" style={{ animationDelay: '150ms' }} />
                       <span className="h-2 w-2 rounded-full bg-zinc-300 dark:bg-zinc-600 animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} className="h-px w-full" />
          </div>
        </main>

        {/* Input Dock (Bottom) */}
        <div className="shrink-0 w-full bg-white dark:bg-zinc-900 pb-3 pt-2 sm:pb-6 z-10 transition-colors duration-300">
          <div className="mx-auto flex w-full max-w-3xl px-3 sm:px-6">
            <div className="relative flex w-full flex-col overflow-hidden rounded-xl sm:rounded-2xl bg-zinc-100 dark:bg-zinc-800 border-none shadow-sm focus-within:ring-2 focus-within:ring-blue-500/50 transition-all duration-300">
              <textarea
                ref={textareaRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Message FluxLink..."
                className="max-h-[200px] min-h-[50px] sm:min-h-[56px] w-full resize-none bg-transparent py-3 sm:py-4 pl-4 sm:pl-5 pr-12 sm:pr-14 text-[16px] sm:text-[15px] leading-relaxed text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-500 dark:placeholder:text-zinc-400 focus:outline-none"
                rows={1}
              />
              
              <div className="absolute bottom-1.5 sm:bottom-2 right-1.5 sm:right-2 flex items-center">
                {(!isTyping && !isAnimating) ? (
                  <button
                    onClick={handleSend}
                    disabled={!inputValue.trim()}
                    className={`flex h-8 w-8 sm:h-10 sm:w-10 items-center justify-center rounded-lg sm:rounded-xl transition-all duration-300 ${
                      inputValue.trim()
                        ? "bg-zinc-900 text-white hover:bg-zinc-800 dark:bg-white dark:text-black dark:hover:bg-zinc-200 active:scale-95"
                        : "bg-transparent text-zinc-400 dark:text-zinc-600 cursor-not-allowed"
                    }`}
                    aria-label="Send message"
                  >
                    <SendIcon className="h-3.5 w-3.5 sm:h-4 w-4" />
                  </button>
                ) : (
                  <button
                    onClick={handleStop}
                    className="flex h-8 w-8 sm:h-10 sm:w-10 items-center justify-center rounded-lg sm:rounded-xl bg-zinc-900 text-white hover:bg-zinc-800 dark:bg-white dark:text-black dark:hover:bg-zinc-200 active:scale-95 transition-all duration-300"
                    aria-label="Stop generation"
                  >
                    <SquareIcon className="h-3.5 w-3.5 sm:h-4 w-4" />
                  </button>
                )}
              </div>
            </div>
          </div>
          <div className="text-center mt-2 px-4">
            <p className="text-[10px] sm:text-[11px] font-medium text-zinc-400 dark:text-zinc-500">
              FluxLink can make mistakes. Consider verifying important information.
            </p>
          </div>
        </div>

      </div>
    </div>
  );
}
