'use client';

import { useState, useRef, useEffect } from 'react';
import { api, SearchResult } from '@/lib/api';

// Helper function for className joining
function cn(...classes: (string | boolean | undefined)[]): string {
  return classes.filter(Boolean).join(' ');
}

// Icons remain the same...
const IconChat = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
  </svg>
);

const IconSend = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
  </svg>
);

const IconClose = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
  </svg>
);

const IconMinimize = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
  </svg>
);

interface Message {
  id: string;
  type: 'user' | 'ai';
  content: string;
  timestamp: Date;
  products?: SearchResult[];
}

interface ChatWidgetProps {
  onClose?: () => void;
}

export default function ChatWidget({ onClose }: ChatWidgetProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'ai',
      content: 'Szia! Építőanyag szakértő asszisztens vagyok. Miben segíthetek? Kérdezhetsz termékekről, műszaki adatokról, vagy alkalmazási területekről.',
      timestamp: new Date(),
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    try {
      // Call the real RAG API
      const searchResponse = await api.searchRAG(userMessage.content, 5);
      
      // Generate AI response based on search results
      const aiContent = generateAIResponse(userMessage.content, searchResponse);
      
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: aiContent,
        timestamp: new Date(),
        products: searchResponse.results.slice(0, 3), // Show top 3 products
      };
      
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('RAG search failed:', error);
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: 'Sajnálom, jelenleg nem tudok kapcsolódni az adatbázishoz. Kérlek próbáld újra később.',
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const generateAIResponse = (userQuery: string, searchResponse: any): string => {
    const { total_results, results } = searchResponse;
    
    if (total_results === 0) {
      return `Sajnálom, nem találtam releváns termékeket a keresett kifejezésre: "${userQuery}". Próbálj meg más kulcsszavakat használni, vagy kérdezz általánosabban az építőanyagokról.`;
    }
    
    const topResult = results[0];
    const query = userQuery.toLowerCase();
    
    // Generate contextual response based on search results
    if (query.includes('hőszigetelés') || query.includes('szigetel')) {
      return `Hőszigeteléshez ${total_results} terméket találtam az adatbázisban. A legjobb találat: **${topResult.name}** (${topResult.category}). Ez a termék ${(topResult.similarity_score * 100).toFixed(0)}%-os egyezést mutat a kereséseddel. Alább láthatod a részleteket és további ajánlásokat.`;
    }
    
    if (query.includes('falazó') || query.includes('tégla')) {
      return `Falazóelemekhez ${total_results} terméket találtam. A legjobb ajánlás: **${topResult.name}**. Az adatbázisból kiderül, hogy ez a termék kiváló választás lehet az építési projektedhez. Nézd meg a műszaki paramétereket alább.`;
    }
    
    if (query.includes('homlokzat') || query.includes('hősz')) {
      return `Homlokzati rendszerekhez ${total_results} terméket ajánlok. A **${topResult.name}** kiemelkedő ${(topResult.similarity_score * 100).toFixed(0)}%-os egyezést mutat. Ezt a terméket gyakran használják professzionális építési projektekben.`;
    }
    
    // Generic response for other queries
    return `A keresésedre "${userQuery}" ${total_results} releváns terméket találtam az adatbázisban. A legjobb találat: **${topResult.name}** (${(topResult.similarity_score * 100).toFixed(0)}% egyezés). Alább láthatod a részletes termékadatokat és további ajánlásokat.`;
  };

  const quickActions = [
    "Hőszigetelés családi házhoz",
    "Homlokzati rendszerek",
    "Tetőszigetelés",
    "ROCKWOOL termékek"
  ];

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        aria-label="AI chat megnyitása"
        className="fixed bottom-6 right-6 w-14 h-14 bg-primary-500 hover:bg-primary-600 text-white rounded-full shadow-strong hover:shadow-xl transition-all duration-300 flex items-center justify-center group z-50"
      >
        <IconChat />
        <div className="absolute -top-2 -left-2 w-3 h-3 bg-accent-500 rounded-full animate-pulse"></div>
      </button>
    );
  }

  return (
    <div className={cn(
      "fixed bottom-6 right-6 w-96 bg-white rounded-2xl shadow-strong border border-neutral-200 z-50 transition-all duration-300",
      isMinimized ? "h-14" : "h-[32rem]"
    )}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-neutral-200">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center text-white">
            <IconChat />
          </div>
          <div>
            <h3 className="font-semibold text-neutral-800">AI Asszisztens</h3>
            <p className="text-xs text-neutral-600">Építőanyag szakértő</p>
          </div>
        </div>
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            aria-label={isMinimized ? "Chat kinyitása" : "Chat minimalizálása"}
            className="p-1 text-neutral-400 hover:text-neutral-600 transition-colors"
          >
            <IconMinimize />
          </button>
          <button
            onClick={() => setIsOpen(false)}
            aria-label="Chat bezárása"
            className="p-1 text-neutral-400 hover:text-neutral-600 transition-colors"
          >
            <IconClose />
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 h-80">
            {messages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  "flex",
                  message.type === 'user' ? "justify-end" : "justify-start"
                )}
              >
                <div
                  className={cn(
                    "max-w-[80%] p-3 rounded-2xl text-sm",
                    message.type === 'user'
                      ? "bg-primary-500 text-white rounded-br-md"
                      : "bg-neutral-100 text-neutral-800 rounded-bl-md"
                  )}
                >
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  
                  {/* Product cards from real search results */}
                  {message.products && message.products.length > 0 && (
                    <div className="mt-3 space-y-2">
                      {message.products.map((product) => (
                        <div
                          key={product.rank}
                          className="bg-white p-3 rounded-lg border border-neutral-200 text-neutral-800"
                        >
                          <h4 className="font-medium text-sm">{product.name}</h4>
                          <p className="text-xs text-neutral-600 mb-2">{product.category}</p>
                          <p className="text-xs text-neutral-700 mb-2">
                            {product.description.length > 100 
                              ? product.description.substring(0, 100) + '...'
                              : product.description
                            }
                          </p>
                          <div className="flex justify-between items-center">
                            <span className="text-xs bg-accent-100 text-accent-700 px-2 py-1 rounded">
                              {(product.similarity_score * 100).toFixed(0)}% egyezés
                            </span>
                            {product.metadata.product_id && (
                              <button
                                onClick={() => window.open(`http://localhost:8000/products/${product.metadata.product_id}/view`, '_blank')}
                                className="text-xs text-primary-600 hover:text-primary-700"
                              >
                                Részletek →
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            
            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-neutral-100 p-3 rounded-2xl rounded-bl-md">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                    <div className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Quick actions */}
          <div className="px-4 py-2 border-t border-neutral-100">
            <div className="flex flex-wrap gap-1">
              {quickActions.map((action, index) => (
                <button
                  key={index}
                  onClick={() => setInputValue(action)}
                  className="text-xs bg-primary-50 text-primary-600 px-2 py-1 rounded-full hover:bg-primary-100 transition-colors"
                >
                  {action}
                </button>
              ))}
            </div>
          </div>

          {/* Input */}
          <form onSubmit={handleSubmit} className="p-4 border-t border-neutral-200">
            <div className="flex space-x-2">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Írj üzenetet..."
                className="flex-1 px-3 py-2 border border-neutral-200 rounded-lg focus:outline-none focus:border-primary-400 text-sm"
                disabled={isTyping}
              />
              <button
                type="submit"
                disabled={!inputValue.trim() || isTyping}
                aria-label="Üzenet küldése"
                className={cn(
                  "p-2 rounded-lg transition-colors",
                  inputValue.trim() && !isTyping
                    ? "bg-primary-500 text-white hover:bg-primary-600"
                    : "bg-neutral-200 text-neutral-400"
                )}
              >
                <IconSend />
              </button>
            </div>
          </form>
        </>
      )}
    </div>
  );
} 