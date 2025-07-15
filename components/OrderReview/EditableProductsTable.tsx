'use client';

import React, { useState } from 'react';
import { Trash2, Plus } from 'lucide-react';
import { OrderProduct } from '../../types/order';

interface EditableProductsTableProps {
  products: OrderProduct[];
  onProductsChange: (products: OrderProduct[]) => void;
}

export function EditableProductsTable({ products, onProductsChange }: EditableProductsTableProps) {
  const [editingCell, setEditingCell] = useState<string | null>(null);

  const updateProduct = (index: number, field: keyof OrderProduct, value: string | number) => {
    const updatedProducts = [...products];
    if (field === 'quantity' || field === 'unitPrice') {
      const numValue = typeof value === 'string' ? parseFloat(value) || 0 : value;
      updatedProducts[index] = {
        ...updatedProducts[index],
        [field]: numValue,
        linePrice: field === 'quantity' 
          ? numValue * updatedProducts[index].unitPrice
          : field === 'unitPrice'
          ? updatedProducts[index].quantity * numValue
          : updatedProducts[index].linePrice
      };
    } else {
      updatedProducts[index] = {
        ...updatedProducts[index],
        [field]: value
      };
    }
    onProductsChange(updatedProducts);
  };

  const deleteProduct = (index: number) => {
    const updatedProducts = products.filter((_, i) => i !== index);
    onProductsChange(updatedProducts);
  };

  const addProduct = () => {
    const newProduct: OrderProduct = {
      id: `NEW${Date.now()}`,
      name: 'Nuevo producto',
      unit: 'Unidad',
      quantity: 1,
      unitPrice: 0,
      linePrice: 0
    };
    onProductsChange([...products, newProduct]);
  };

  const totalAmount = products.reduce((sum, product) => sum + product.linePrice, 0);

  const renderEditableCell = (
    value: string | number,
    productIndex: number,
    field: keyof OrderProduct,
    cellId: string
  ) => {
    const isEditing = editingCell === cellId;
    const isNumeric = field === 'quantity' || field === 'unitPrice';

    if (isEditing) {
      return (
        <input
          type={isNumeric ? 'number' : 'text'}
          value={value}
          onChange={(e) => updateProduct(productIndex, field, e.target.value)}
          onBlur={() => setEditingCell(null)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              setEditingCell(null);
            }
          }}
          className="w-full px-2 py-1 text-sm border border-blue-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
          autoFocus
        />
      );
    }

    return (
      <div
        onClick={() => setEditingCell(cellId)}
        className="cursor-pointer hover:bg-gray-50 px-2 py-1 rounded text-sm min-h-[24px] flex items-center"
      >
        {field === 'unitPrice' || field === 'linePrice' ? `€ ${Number(value).toFixed(2)}` : value}
      </div>
    );
  };

  return (
    <div className="space-y-4">
      <div className="overflow-x-auto">
        <table className="w-full border border-gray-200 rounded-lg">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase tracking-wider border-b">
                Producto
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase tracking-wider border-b">
                Unidad
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase tracking-wider border-b">
                Cantidad
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase tracking-wider border-b">
                Precio unitario
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase tracking-wider border-b">
                Precio de línea
              </th>
              <th className="px-3 py-2 text-center text-xs font-medium text-gray-700 uppercase tracking-wider border-b w-12">
                
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {products.map((product, index) => (
              <tr key={product.id} className="hover:bg-gray-50">
                <td className="px-3 py-2 border-b">
                  <div className="flex flex-col">
                    <span className="text-xs text-gray-500">{product.id}</span>
                    {renderEditableCell(product.name, index, 'name', `${product.id}-name`)}
                  </div>
                </td>
                <td className="px-3 py-2 border-b">
                  {renderEditableCell(product.unit, index, 'unit', `${product.id}-unit`)}
                </td>
                <td className="px-3 py-2 border-b text-center">
                  {renderEditableCell(product.quantity, index, 'quantity', `${product.id}-quantity`)}
                </td>
                <td className="px-3 py-2 border-b">
                  {renderEditableCell(product.unitPrice, index, 'unitPrice', `${product.id}-unitPrice`)}
                </td>
                <td className="px-3 py-2 border-b">
                  {renderEditableCell(product.linePrice, index, 'linePrice', `${product.id}-linePrice`)}
                </td>
                <td className="px-3 py-2 border-b text-center">
                  <button
                    onClick={() => deleteProduct(index)}
                    className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add Product Button */}
      <div className="flex items-center justify-between">
        <button
          onClick={addProduct}
          className="flex items-center space-x-2 text-blue-600 hover:text-blue-700 text-sm"
        >
          <Plus className="w-4 h-4" />
          <span>Agregar productos</span>
        </button>

        {/* Total */}
        <div className="text-right">
          <span className="text-sm font-medium text-gray-900">
            Precio total: €{totalAmount.toFixed(2)}
          </span>
        </div>
      </div>
    </div>
  );
}