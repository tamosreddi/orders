'use client';

import { ChevronLeft, ChevronRight, ChevronDown } from 'lucide-react';

interface TablePaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
}

export function TablePagination({
  currentPage,
  totalPages,
  totalItems,
  pageSize,
  onPageChange,
  onPageSizeChange
}: TablePaginationProps) {
  const startItem = (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalItems);

  const pageSizeOptions = [10, 25, 50, 100];

  return (
    <div className="flex items-center justify-between py-4 px-2">
      {/* Rows per page */}
      <div className="flex items-center space-x-2">
        <span className="text-sm text-text-muted">Rows per page:</span>
        <div className="relative">
          <select
            value={pageSize}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
            className="appearance-none bg-white border border-gray-300 rounded px-3 py-1 pr-8 text-sm focus:outline-none focus:ring-1 focus:ring-brand-navy-900 focus:border-brand-navy-900"
          >
            {pageSizeOptions.map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
          <ChevronDown size={16} className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 pointer-events-none" />
        </div>
      </div>

      {/* Items info and pagination controls */}
      <div className="flex items-center space-x-6">
        {/* Items info */}
        <span className="text-sm text-text-muted">
          {totalItems} items • {totalPages} pages
        </span>

        {/* Pagination controls */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage <= 1}
            className={`
              p-1 rounded transition-colors
              ${currentPage <= 1 
                ? 'text-gray-300 cursor-not-allowed' 
                : 'text-text-muted hover:text-text-default hover:bg-gray-100'
              }
            `}
          >
            <ChevronLeft size={20} />
          </button>

          <span className="text-sm font-medium text-text-default">
            {currentPage}
          </span>

          <button
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage >= totalPages}
            className={`
              p-1 rounded transition-colors
              ${currentPage >= totalPages 
                ? 'text-gray-300 cursor-not-allowed' 
                : 'text-text-muted hover:text-text-default hover:bg-gray-100'
              }
            `}
          >
            <ChevronRight size={20} />
          </button>
        </div>
      </div>
    </div>
  );
}