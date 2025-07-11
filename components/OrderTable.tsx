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
} from '@tanstack/react-table';
import { ChevronUp, ChevronDown } from 'lucide-react';
import { Order } from '../types/order';
import { OrderStatusBadge } from './OrderStatusBadge';

interface OrderTableProps {
  orders: Order[];
  onRowClick: (order: Order) => void;
  onBulkConfirm: (selectedOrderIds: string[]) => void;
}

export function OrderTable({ orders, onRowClick, onBulkConfirm }: OrderTableProps) {
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
  const [sorting, setSorting] = useState<SortingState>([]);

  // Stable reference to prevent re-renders
  const data = useMemo(() => orders, [orders]);

  const columnHelper = createColumnHelper<Order>();

  const columns = useMemo(() => [
    // Selection column
    columnHelper.display({
      id: 'select',
      header: ({ table }) => (
        <input
          type="checkbox"
          className="rounded border-surface-border text-brand-navy-900 focus:ring-brand-navy-900"
          checked={table.getIsAllRowsSelected()}
          onChange={table.getToggleAllRowsSelectedHandler()}
          aria-label="Select all orders"
        />
      ),
      cell: ({ row }) => (
        <input
          type="checkbox"
          className="rounded border-surface-border text-brand-navy-900 focus:ring-brand-navy-900"
          checked={row.getIsSelected()}
          onChange={row.getToggleSelectedHandler()}
          aria-label={`Select order ${row.original.id}`}
        />
      ),
      enableSorting: false,
    }),

    // Order # column
    columnHelper.accessor('id', {
      header: 'Order #',
      cell: (info) => (
        <span className="font-medium text-text-default">{info.getValue()}</span>
      ),
    }),

    // Customer column with avatar
    columnHelper.accessor('customer', {
      header: 'Customer',
      cell: (info) => {
        const customer = info.getValue();
        return (
          <div className="flex items-center space-x-3">
            <Image
              src={customer.avatar}
              alt={customer.name}
              width={32}
              height={32}
              className="rounded-full"
            />
            <span className="text-text-default">{customer.name}</span>
          </div>
        );
      },
      sortingFn: (rowA, rowB) =>
        rowA.original.customer.name.localeCompare(rowB.original.customer.name),
    }),

    // Channel column
    columnHelper.accessor('channel', {
      header: 'Channel',
      cell: (info) => {
        const channel = info.getValue();
        return (
          <span className="text-caption text-text-muted uppercase">
            {channel}
          </span>
        );
      },
    }),

    // Order Date column
    columnHelper.accessor('orderDate', {
      header: 'Order Date',
      cell: (info) => {
        const date = new Date(info.getValue());
        return (
          <span className="text-text-default">
            {date.toLocaleDateString('en-US', { 
              month: 'short', 
              day: 'numeric', 
              year: 'numeric' 
            })}
          </span>
        );
      },
    }),

    // Products column
    columnHelper.accessor('products', {
      header: 'Products',
      cell: (info) => (
        <span className="text-text-default">{info.getValue()}</span>
      ),
    }),

    // Order Status column
    columnHelper.accessor('status', {
      header: 'Order Status',
      cell: (info) => <OrderStatusBadge status={info.getValue()} />,
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
    onRowSelectionChange: setRowSelection,
    onSortingChange: setSorting,
  });

  const selectedOrderIds = Object.keys(rowSelection).filter(key => rowSelection[key])
    .map(index => orders[parseInt(index)]?.id).filter(Boolean);

  const handleBulkConfirm = () => {
    if (selectedOrderIds.length > 0) {
      onBulkConfirm(selectedOrderIds);
    }
  };

  return (
    <div className="space-y-4">
      {/* Bulk Actions Bar */}
      {selectedOrderIds.length > 0 && (
        <div className="flex items-center justify-between p-4 bg-brand-navy-50 rounded-md">
          <span className="text-body text-text-default">
            {selectedOrderIds.length} order{selectedOrderIds.length !== 1 ? 's' : ''} selected
          </span>
          <button
            onClick={handleBulkConfirm}
            className="px-4 py-2 bg-state-success text-white rounded-md hover:opacity-90 transition-opacity duration-fast"
          >
            Confirm Orders
          </button>
        </div>
      )}

      {/* Table Container */}
      <div className="overflow-x-auto lg:overflow-x-visible">
        <table className="min-w-full divide-y divide-surface-border">
          {/* Table Header */}
          <thead className="bg-surface-alt">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-4 py-3 text-left text-caption font-medium text-text-muted uppercase tracking-wider"
                  >
                    {header.isPlaceholder ? null : (
                      <div
                        className={`flex items-center space-x-2 ${
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
                                  ? 'text-brand-navy-900'
                                  : 'text-text-muted'
                              }`}
                            />
                            <ChevronDown
                              className={`h-3 w-3 -mt-1 ${
                                header.column.getIsSorted() === 'desc'
                                  ? 'text-brand-navy-900'
                                  : 'text-text-muted'
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
          <tbody className="bg-surface-0 divide-y divide-surface-border">
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                className="hover:bg-surface-alt cursor-pointer transition-colors duration-fast"
                onClick={() => onRowClick(row.original)}
              >
                {row.getVisibleCells().map((cell) => (
                  <td
                    key={cell.id}
                    className="px-4 py-4 whitespace-nowrap"
                    onClick={(e) => {
                      // Prevent row click when clicking checkbox
                      if (cell.column.id === 'select') {
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
        {orders.length === 0 && (
          <div className="text-center py-8">
            <p className="text-text-muted">No orders found</p>
          </div>
        )}
      </div>
    </div>
  );
}