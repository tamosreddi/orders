//used in Customers page to display the customers in a table

'use client';

import React, { useState, useMemo } from 'react';
import Image from 'next/image';
import {
  useReactTable,
  createColumnHelper,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  RowSelectionState,
  SortingState,
  OnChangeFn,
} from '@tanstack/react-table';
import { ChevronUp, ChevronDown, MessageCircle } from 'lucide-react';
import { Customer } from '../../types/customer';
import { CustomerStatusBadge } from './CustomerStatusBadge';
import { CustomerLabels } from './CustomerLabels';

interface CustomerTableProps {
  customers: Customer[];
  rowSelection: RowSelectionState;
  onRowSelectionChange: OnChangeFn<RowSelectionState>;
  onCustomerSelect: (customer: Customer) => void;
}

export function CustomerTable({ 
  customers, 
  rowSelection, 
  onRowSelectionChange,
  onCustomerSelect 
}: CustomerTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);

  // Stable reference to prevent re-renders
  const data = useMemo(() => customers, [customers]);

  const columnHelper = createColumnHelper<Customer>();

  const columns = useMemo(() => [
    // Selection column
    columnHelper.display({
      id: 'select',
      header: ({ table }) => (
        <input
          type="checkbox"
          className="rounded border-gray-300 text-brand-navy-900 focus:ring-brand-navy-900"
          checked={table.getIsAllRowsSelected()}
          onChange={table.getToggleAllRowsSelectedHandler()}
          aria-label="Select all customers"
        />
      ),
      cell: ({ row }) => (
        <input
          type="checkbox"
          className="rounded border-gray-300 text-brand-navy-900 focus:ring-brand-navy-900"
          checked={row.getIsSelected()}
          onChange={row.getToggleSelectedHandler()}
          aria-label={`Select customer ${row.original.id}`}
        />
      ),
      enableSorting: false,
    }),

    // Customer Info column
    columnHelper.accessor('name', {
      header: 'Customer info',
      cell: (info) => {
        const customer = info.row.original;
        return (
          <div className="flex items-center space-x-3">
            <Image
              src={customer.avatar}
              alt={customer.name}
              width={32}
              height={32}
              className="rounded-full"
            />
            <div className="flex flex-col">
              <span className="text-xs text-text-muted">{customer.code}</span>
              <span className="text-sm text-text-default font-medium">{customer.name}</span>
            </div>
          </div>
        );
      },
      sortingFn: (rowA, rowB) =>
        rowA.original.name.localeCompare(rowB.original.name),
    }),

    // Labels column
    columnHelper.accessor('labels', {
      header: 'Labels',
      cell: (info) => <CustomerLabels labels={info.getValue()} />,
      enableSorting: false,
    }),

    // Last ordered column
    columnHelper.accessor('lastOrdered', {
      header: 'Last ordered',
      cell: (info) => {
        const date = info.getValue();
        if (!date) return <span className="text-gray-400">-</span>;
        
        const formattedDate = new Date(date).toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric'
        });
        
        return (
          <span className="text-sm text-blue-600 underline cursor-pointer hover:text-blue-700">
            {formattedDate}
          </span>
        );
      },
      sortingFn: (rowA, rowB) => {
        const dateA = rowA.original.lastOrdered;
        const dateB = rowB.original.lastOrdered;
        if (!dateA && !dateB) return 0;
        if (!dateA) return 1;
        if (!dateB) return -1;
        return new Date(dateA).getTime() - new Date(dateB).getTime();
      },
    }),

    // Expected order column
    columnHelper.accessor('expectedOrder', {
      header: 'Expected order',
      cell: (info) => {
        const date = info.getValue();
        if (!date) return <span className="text-gray-400">-</span>;
        
        const formattedDate = new Date(date).toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric'
        });
        
        return (
          <span className="text-sm text-text-default">
            {formattedDate}
          </span>
        );
      },
      sortingFn: (rowA, rowB) => {
        const dateA = rowA.original.expectedOrder;
        const dateB = rowB.original.expectedOrder;
        if (!dateA && !dateB) return 0;
        if (!dateA) return 1;
        if (!dateB) return -1;
        return new Date(dateA).getTime() - new Date(dateB).getTime();
      },
    }),

    // Status column
    columnHelper.accessor('status', {
      header: 'Status',
      cell: (info) => <CustomerStatusBadge status={info.getValue()} />,
      enableSorting: false,
    }),

    // Actions column
    columnHelper.display({
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => (
        <button
          className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
          disabled
          title="Message customer (coming soon)"
        >
          <MessageCircle className="w-4 h-4" />
        </button>
      ),
      enableSorting: false,
    }),
  ], [columnHelper]);

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    enableRowSelection: true,
    state: {
      rowSelection,
      sorting,
    },
    onRowSelectionChange,
    onSortingChange: setSorting,
  });

  return (
    <div className="overflow-x-auto lg:overflow-x-visible">
      <table className="min-w-full divide-y divide-gray-200">
        {/* Table Header */}
        <thead className="bg-gray-50">
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th
                  key={header.id}
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  {header.isPlaceholder ? null : (
                    <div
                      className={`flex items-center space-x-1 ${
                        header.column.getCanSort() ? 'cursor-pointer select-none' : ''
                      }`}
                      onClick={header.column.getToggleSortingHandler()}
                    >
                      <span>
                        {flexRender(header.column.columnDef.header, header.getContext())}
                      </span>
                      {header.column.getCanSort() && (
                        <div className="flex flex-col">
                          <ChevronUp
                            className={`h-3 w-3 ${
                              header.column.getIsSorted() === 'asc'
                                ? 'text-gray-900'
                                : 'text-gray-300'
                            }`}
                          />
                          <ChevronDown
                            className={`h-3 w-3 -mt-1 ${
                              header.column.getIsSorted() === 'desc'
                                ? 'text-gray-900'
                                : 'text-gray-300'
                            }`}
                          />
                        </div>
                      )}
                    </div>
                  )}
                </th>
              ))}
            </tr>
          ))}
        </thead>

        {/* Table Body */}
        <tbody className="bg-white divide-y divide-gray-200">
          {table.getRowModel().rows.map((row) => (
            <tr
              key={row.id}
              className="hover:bg-gray-50 transition-colors duration-fast cursor-pointer"
              onClick={() => onCustomerSelect(row.original)}
            >
              {row.getVisibleCells().map((cell) => (
                <td
                  key={cell.id}
                  className="px-6 py-4 whitespace-nowrap"
                  onClick={(e) => {
                    // Prevent row click when clicking checkbox or actions
                    if (cell.column.id === 'select' || cell.column.id === 'actions') {
                      e.stopPropagation();
                    }
                  }}
                >
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      {/* Empty State */}
      {customers.length === 0 && (
        <div className="text-center py-8">
          <p className="text-text-muted">No customers found</p>
        </div>
      )}
    </div>
  );
}