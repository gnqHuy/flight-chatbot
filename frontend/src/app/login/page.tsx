'use client';

import { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import {
  Edit2,
  ThumbsUp,
  ThumbsDown,
  Copy,
  MessageSquare,
  Info,
  ArrowRight,
  Eye,
  EyeOff,
} from 'lucide-react';
import { FcGoogle } from 'react-icons/fc';
import { FaApple } from 'react-icons/fa';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';

const BotIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path
      d="M4.66667 6.66667V5.33333C4.66667 4.59695 4.95639 3.89075 5.47214 3.375C5.98788 2.85924 6.69409 2.56952 7.43048 2.56952C8.16686 2.56952 8.87307 2.85924 9.38881 3.375C9.90456 3.89075 10.1943 4.59695 10.1943 5.33333V6.66667"
      stroke="white"
      strokeWidth="1.33333"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <rect
      x="2"
      y="6.66667"
      width="12"
      height="6"
      rx="3"
      stroke="white"
      strokeWidth="1.33333"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M6 10H10"
      stroke="white"
      strokeWidth="1.33333"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <circle cx="6" cy="8" r="0.666667" fill="white" />
    <circle cx="10" cy="8" r="0.666667" fill="white" />
    <path
      d="M2.66667 9.33333L0.666667 10.6667V13.3333L2.66667 12V9.33333Z"
      stroke="white"
      strokeWidth="1.33333"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M13.3333 9.33333L15.3333 10.6667V13.3333L13.3333 12V9.33333Z"
      stroke="white"
      strokeWidth="1.33333"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export default function LoginPage() {
  const [isLoginView, setIsLoginView] = useState(true);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { login, signup } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      if (isLoginView) {
        await login(email, password);
      } else {
        await signup(email, password, fullName);
      }
    } catch (err: any) {
      setError(
        isLoginView
          ? 'Email hoặc mật khẩu không chính xác.'
          : err.response?.data?.detail || 'Đăng ký thất bại. Vui lòng thử lại.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const toggleView = () => {
    setIsLoginView(!isLoginView);
    setError('');
    setEmail('');
    setPassword('');
    setFullName('');
  };

  return (
    <div className="flex min-h-screen bg-white">
      <div className="relative  from-primary via-brand-purple to-brand-pink hidden justify-between flex-col bg-gradient-to-br p-12 lg:flex lg:w-[50%]">
        <div className="mb-10">
          <div className="mb-3 text-[14px] font-medium tracking-widest text-white uppercase">
            Flight Chatbot
          </div>
          <h1 className="mb-2 max-w-2xl text-4xl leading-tight font-bold text-white">
            Tìm kiếm, So sánh & Lựa chọn
          </h1>
          <h1 className="max-w-2xl text-end text-4xl leading-tight font-bold text-white">
            chuyến bay dễ dàng cùng AI
          </h1>
        </div>

        <div className="space-y-5 rounded-3xl p-6 text-[12px] text-white">
          <div className="flex items-center gap-3">
            <div className="max-w-[90%] rounded-3xl rounded-tl-none p-5 text-[13px] text-white/90">
              <p className="mb-1">
                Xin chào! Tôi là trợ lý AI hỗ trợ tìm kiếm và tư vấn vé máy bay thông minh. Bạn có
                thể trò chuyện với tôi bằng ngôn ngữ tự nhiên để tìm chuyến bay phù hợp, so sánh các
                lựa chọn và tra cứu thông tin hàng không một cách nhanh chóng.
              </p><br/>
              <ol className="list-outside list-decimal space-y-2 pl-5">
                <li>
                  <b>Tìm kiếm vé máy bay:</b> Hỗ trợ tra cứu chuyến bay theo điểm đi, điểm đến, ngày
                  bay, số lượng hành khách và hạng ghế với dữ liệu được cập nhật theo thời gian
                  thực.
                </li>

                <li>
                  <b>Lọc và sắp xếp kết quả:</b> Cho phép lọc chuyến bay theo hãng hàng không, mức
                  giá, giờ khởi hành, thời lượng bay, số điểm dừng hoặc lựa chọn bay thẳng.
                </li>

                <li>
                  <b>Phân tích và so sánh chuyến bay:</b> Hỗ trợ đánh giá ưu và nhược điểm giữa các
                  hãng hoặc các lựa chọn vé dựa trên giá vé, hành lý, thời gian bay và tiện ích đi
                  kèm.
                </li>

                <li>
                  <b>Tra cứu chính sách hàng không:</b> Cung cấp thông tin về hành lý xách tay, hành
                  lý ký gửi, đổi vé, hoàn vé, check-in và các quy định đặc biệt của từng hãng bay.
                </li>

                <li>
                  <b>Tra cứu khuyến mãi:</b> Tìm kiếm các chương trình ưu đãi, mã giảm giá và khuyến
                  mãi vé máy bay đang còn hiệu lực theo nhu cầu của bạn.
                </li>
              </ol><br/>
              <p className="mt-1 text-white/80">
                Bạn chỉ cần nhập yêu cầu bằng ngôn ngữ tự nhiên, hệ thống sẽ tự động phân tích, tìm
                kiếm dữ liệu phù hợp và đưa ra phản hồi trực quan ngay trong cuộc trò chuyện.
              </p>
            </div>

            <div className="flex flex-col items-center gap-1 self-center">
              <Button variant="icon">
                <ThumbsUp size={18} />
              </Button>
              <Button variant="icon">
                <ThumbsDown size={18} />
              </Button>
              <Button variant="icon">
                <Copy size={18} />
              </Button>
              <Button variant="icon">
                <MessageSquare size={18} />
              </Button>
              <Button variant="icon">
                <Info size={18} />
              </Button>
            </div>
          </div>
          <div className="flex items-center gap-3 rounded-2xl bg-white/10 p-3 text-white/50 backdrop-blur-sm">
            <Button variant="ghost">
              <BotIcon />
            </Button>
            <span className="flex-1 cursor-text">Reply...</span>
            <button className="bg-primary hover:bg-primary-hover flex h-8 w-8 items-center justify-center rounded-full transition-colors">
              <ArrowRight size={18} className="text-white" />
            </button>
          </div>
        </div>

        
      </div>

      <div className="flex w-full items-center justify-center px-10 py-16 lg:w-[50%]">
        <div className="w-full max-w-[60%] space-y-12 lg:max-w-[70%] xl:max-w-[50%]">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-gray-950">
              {isLoginView ? 'Đăng nhập' : 'Đăng ký tài khoản'}
            </h2>
            <p className="mt-3 text-sm text-gray-600">
              {isLoginView
                ? 'Truy cập Flight Chatbot ngay'
                : 'Tham gia cùng chúng tôi để trải nghiệm ngay'}
            </p>
          </div>

          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-600">
              {error}
            </div>
          )}

          <form
            className="animate-in fade-in slide-in-from-bottom-2 space-y-6 duration-300"
            onSubmit={handleSubmit}
          >
            {!isLoginView && (
              <Input
                id="fullName"
                type="text"
                label="Full Name*"
                placeholder="John Doe"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />
            )}

            <Input
              id="email"
              type="email"
              label="Email Address*"
              placeholder="ex.email@domain.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />

            <Input
              id="password"
              type={showPassword ? 'text' : 'password'}
              label="Password*"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              icon={showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              onIconClick={() => setShowPassword(!showPassword)}
            />

            <Button type="submit" variant="primary" disabled={isSubmitting}>
              {isSubmitting ? 'Đang xử lý...' : isLoginView ? 'Đăng nhập' : 'Tạo tài khoản'}
            </Button>
          </form>

          <div className="text-center text-sm text-gray-600">
            {isLoginView ? "Don't have an account? " : 'Already have an account? '}
            <button
              onClick={toggleView}
              className="text-primary cursor-pointer border-none bg-transparent p-0 font-semibold hover:underline"
            >
              {isLoginView ? 'Sign Up' : 'Log In'}
            </button>
          </div>

          <div className="relative flex justify-center text-sm">
            <div className="absolute inset-0 flex items-center">
              <div className="border-surface-border w-full border-t" />
            </div>
            <span className="relative bg-white px-3 text-gray-500">Or continue with</span>
          </div>

          <div className="flex space-x-4">
            <Button type="button" variant="outline">
              <FcGoogle size={22} /> Google
            </Button>
            <Button type="button" variant="outline">
              <FaApple size={22} /> Apple
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
