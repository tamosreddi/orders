'use client';

import React, { useState, useMemo } from 'react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
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
import { ChevronUp, ChevronDown } from 'lucide-react';
import { Order } from '../types/order';
import { OrderStatusBadge } from './OrderStatusBadge';

interface OrderTableProps {
  orders: Order[];
  rowSelection: RowSelectionState;
  onRowSelectionChange: OnChangeFn<RowSelectionState>;
}

export function OrderTable({ orders, rowSelection, onRowSelectionChange }: OrderTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const router = useRouter();

  // Stable reference to prevent re-renders
  const data = useMemo(() => orders, [orders]);

  const handleRowClick = (orderId: string) => {
    router.push(`/orders/${orderId}/review`);
  };

  const columnHelper = createColumnHelper<Order>();

  const columns = useMemo(() => [
    // Selection column
    columnHelper.display({
      id: 'select',
      header: ({ table }) => (
        <input
          type="checkbox"
          className="w-4 h-4 rounded border-gray-300 text-reddi-navyblue focus:ring-reddi-navyblue"
          checked={table.getIsAllRowsSelected()}
          onChange={table.getToggleAllRowsSelectedHandler()}
          aria-label="Select all orders"
        />
      ),
      cell: ({ row }) => (
        <input
          type="checkbox"
          className="w-4 h-4 rounded border-gray-300 text-reddi-navyblue focus:ring-reddi-navyblue"
          checked={row.getIsSelected()}
          onChange={row.getToggleSelectedHandler()}
          aria-label={`Select order ${row.original.id}`}
        />
      ),
      enableSorting: false,
    }),

    // Customer column with code and name
    columnHelper.accessor('customer', {
      header: 'Cliente',
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
            <div className="flex flex-col">
              <span className="text-xs text-text-muted">{customer.code}</span>
              <span className="text-sm text-text-default font-medium">{customer.name}</span>
            </div>
          </div>
        );
      },
      sortingFn: (rowA, rowB) =>
        rowA.original.customer.name.localeCompare(rowB.original.customer.name),
    }),

    // Received column with date and time
    columnHelper.accessor('receivedDate', {
      header: 'Recibida',
      cell: (info) => {
        const order = info.row.original;
        const date = new Date(info.getValue());
        return (
          <div className="flex flex-col">
            <span className="text-sm text-text-default">
              {date.toLocaleDateString('en-US', { 
                day: 'numeric',
                month: 'short'
              })}
            </span>
            <span className="text-xs text-text-muted">{order.receivedTime}</span>
          </div>
        );
      },
      sortingFn: (rowA, rowB) =>
        new Date(rowA.original.receivedDate).getTime() - new Date(rowB.original.receivedDate).getTime(),
    }),

    // Delivery Date column
    columnHelper.accessor('deliveryDate', {
      header: 'Fecha de Envío',
      cell: (info) => {
        const deliveryDate = info.getValue();
        if (!deliveryDate) {
          return (
            <span className="text-sm text-text-muted">
              Fecha por confirmar
            </span>
          );
        }
        
        const date = new Date(deliveryDate);
        if (isNaN(date.getTime())) {
          return (
            <span className="text-sm text-text-muted">
              Fecha por confirmar
            </span>
          );
        }
        
        return (
          <span className="text-sm text-text-default">
            {date.toLocaleDateString('en-US', { 
              weekday: 'short',
              day: 'numeric',
              month: 'short',
              year: 'numeric'
            })}
          </span>
        );
      },
      sortingFn: (rowA, rowB) =>
        new Date(rowA.original.deliveryDate).getTime() - new Date(rowB.original.deliveryDate).getTime(),
    }),

    // Products ordered column
    columnHelper.accessor('products', {
      header: 'Productos',
      cell: (info) => (
        <span className="text-sm text-text-default text-center">{info.getValue()}</span>
      ),
    }),

    // Status column
    columnHelper.accessor('status', {
      header: 'Estatus',
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
              onClick={() => handleRowClick(row.original.id)}
            >
              {row.getVisibleCells().map((cell) => (
                <td
                  key={cell.id}
                  className="px-6 py-4 whitespace-nowrap"
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
  );
}