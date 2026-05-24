'use client';

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

type Props = {
  content: string;
};

const MarkdownRenderer: React.FC<Props> = ({ content }) => {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        // Tùy biến Text bình thường
        p: ({ node, ...props }) => <p className="mb-3 text-slate-700 leading-relaxed" {...props} />,
        
        // Tùy biến Danh sách
        ul: ({ node, ...props }) => <ul className="mb-4 ml-6 list-outside list-disc space-y-2 text-slate-700" {...props} />,
        li: ({ node, ...props }) => <li className="pl-1" {...props} />,
        
        // Tùy biến In đậm
        strong: ({ node, ...props }) => <strong className="font-bold text-slate-900" {...props} />,

        // 🌟 TÙY BIẾN BẢNG (TABLE) CỰC ĐẸP
        table: ({ node, ...props }) => (
          <div className="my-5 w-full overflow-x-auto rounded-xl border border-slate-200 shadow-sm">
            <table className="w-full text-left text-[18px]" {...props} />
          </div>
        ),
        thead: ({ node, ...props }) => (
          <thead className="bg-slate-50 text-slate-600" {...props} />
        ),
        th: ({ node, ...props }) => (
          <th className="border-b border-slate-200 px-4 py-3 font-semibold whitespace-nowrap" {...props} />
        ),
        td: ({ node, ...props }) => (
          <td className="border-b border-slate-100 px-4 py-3 align-top text-slate-700 last:border-b-0" {...props} />
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  );
};

export default MarkdownRenderer;