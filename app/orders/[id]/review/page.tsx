'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { X } from 'lucide-react';
import { OrderDetails, OrderProduct } from '../../../../types/order';
import { getOrderDetails } from '../../../../lib/mockOrders';
import { EditableProductsTable } from '../../../../components/OrderReview/EditableProductsTable';

export default function OrderReviewPage() {
  const params = useParams();
  const router = useRouter();
  const orderId = params.id as string;
  
  const [orderDetails, setOrderDetails] = useState<OrderDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [products, setProducts] = useState<OrderProduct[]>([]);
  const [comment, setComment] = useState('');

  useEffect(() => {
    const loadOrderDetails = async () => {
      try {
        const details = await getOrderDetails(orderId);
        if (details) {
          setOrderDetails(details);
          setProducts(details.products);
          setComment(details.additionalComment);
        }
      } catch (error) {
        console.error('Error loading order details:', error);
      } finally {
        setLoading(false);
      }
    };

    loadOrderDetails();
  }, [orderId]);

  const handleClose = () => {
    router.push('/orders');
  };

  const handleProductsChange = (updatedProducts: OrderProduct[]) => {
    setProducts(updatedProducts);
  };

  const handleAccept = () => {
    // TODO: Implement order acceptance
    console.log('Accepting order with products:', products);
    router.push('/orders');
  };

  const handleReject = () => {
    // TODO: Implement order rejection
    console.log('Rejecting order');
    router.push('/orders');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-600">Cargando detalles del pedido...</div>
      </div>
    );
  }

  if (!orderDetails) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-red-600">Error: No se pudo cargar el pedido</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-6 h-6 bg-orange-500 rounded-full flex items-center justify-center">
              <span className="text-white text-xs font-medium">📍</span>
            </div>
            <span className="text-sm text-gray-600">En revisión</span>
            <span className="text-sm text-gray-400">2 de 54 pedidos</span>
          </div>
          <div className="flex items-center space-x-4">
            <button className="text-blue-600 text-sm hover:text-blue-700">
              Guardar y Salir
            </button>
            <button 
              onClick={handleClose}
              className="p-1 hover:bg-gray-100 rounded"
            >
              <X className="w-5 h-5 text-gray-400" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex h-[calc(100vh-80px)]">
        {/* Left Side - WhatsApp Display */}
        <div className="w-1/2 bg-white border-r border-gray-200 flex flex-col">
          {/* WhatsApp Header - Fixed */}
          <div className="bg-teal-600 text-white p-3 flex items-center space-x-3 flex-shrink-0">
            <div className="w-8 h-8 bg-gray-300 rounded-full"></div>
            <div>
              <div className="font-medium">Restaurante San Juan</div>
              <div className="text-xs opacity-75">Vie, Jul 26</div>
            </div>
          </div>
          
          {/* Chat Messages - Scrollable */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
            <div className="bg-white rounded-lg p-3 max-w-xs">
              <p className="text-sm whitespace-pre-line">
                {orderDetails.whatsappMessage}
              </p>
              <div className="text-xs text-gray-500 mt-2">{orderDetails.receivedTime}</div>
            </div>
            
            <div className="bg-white rounded-lg p-3 max-w-xs">
              <p className="text-sm">¿Puedes añadir también yogur griego?</p>
              <div className="flex items-center space-x-1 text-xs text-gray-500 mt-2">
                <span>OK</span>
                <div className="flex space-x-0.5">
                  <div className="w-1 h-1 bg-blue-500 rounded-full"></div>
                  <div className="w-1 h-1 bg-blue-500 rounded-full"></div>
                </div>
              </div>
            </div>
          </div>

          {/* Attachments Section - Fixed */}
          <div className="border-t p-4 bg-white flex-shrink-0">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Adjuntos</h4>
            <div className="space-y-2">
              {orderDetails.attachments.map((attachment, index) => (
                <div key={index} className="bg-gray-50 rounded p-3">
                  <div className="flex items-center space-x-2 text-sm text-gray-600">
                    <span>📎</span>
                    <span>{attachment}</span>
                    <button className="text-blue-600 hover:text-blue-700 ml-auto">
                      Descargar
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Side - Order Details */}
        <div className="w-1/2 bg-white flex flex-col">
          {/* Review Notice - Fixed at top */}
          <div className="bg-gray-100 border-b border-gray-200 shadow-sm">
            <div className="p-4 flex items-start space-x-3">
              <div className="w-5 h-3 text-gray-600 mt-0.5">
                ℹ️
              </div>
              <p className="text-sm text-gray-700">
                Revise todos los elementos con cuidado: los resultados de la IA no siempre son precisos.
              </p>
            </div>
          </div>

          {/* Fixed Top Section */}
          <div className="p-6 flex-shrink-0">

            {/* Order Info */}
            <div className="grid grid-cols-2 gap-6 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1">
                  Recibido el
                </label>
                <div className="text-sm text-gray-800">
                  {new Date(orderDetails.receivedDate).toLocaleDateString('es-ES', { 
                    day: 'numeric', 
                    month: 'long', 
                    year: 'numeric' 
                  })} • {orderDetails.receivedTime}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1">
                  Enviado desde
                </label>
                <div className="text-sm text-blue-600">pedidos@finhshop.com</div>
              </div>
            </div>

            {/* Customer Info */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-500 mb-2">
                Cliente
              </label>
              <input
                type="text"
                defaultValue={`${orderDetails.customer.name} (${orderDetails.customer.code}), ${orderDetails.customer.address}`}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              />
            </div>

            {/* Delivery Date and Postal Code */}
            <div className="grid grid-cols-2 gap-4 mb-2">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Fecha de entrega
                </label>
                <input
                  type="text"
                  defaultValue={new Date(orderDetails.deliveryDate).toLocaleDateString('es-ES')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Número postal
                </label>
                <input
                  type="text"
                  defaultValue={orderDetails.postalCode}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
              </div>
            </div>

            {/* 
            // Requirements Notice (oculto temporalmente)
            <div className="flex items-start space-x-3 mb-4">
              <div className="w-5 h-5 text-blue-500 mt-0.5">
                📦
              </div>
              <p className="text-sm text-gray-700">
                Los plazos de entrega deben acordarse con antelación y cumplir con los horarios de HOC CS. Los términos y condiciones de HOC CS tienen prioridad en todo momento.
              </p>
            </div>
            */}
          </div>

          {/* Scrollable Bottom Section */}
          <div className="flex-1 overflow-y-auto px-6">
            {/* Products Table */}
            <div className="mb-6">
              <EditableProductsTable 
                products={products} 
                onProductsChange={handleProductsChange}
              />
            </div>

            {/* Comment Section */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Comentario adicional
              </label>
              <div className="text-xs text-gray-500 mb-1">Se agregará a su ERP como comentario del pedido</div>
              <textarea
                placeholder="Introduce tu comentario aquí"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              />
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end space-x-4 pb-8">
              <button 
                onClick={handleReject}
                className="px-6 py-2 border border-red-300 text-red-700 rounded-md hover:bg-red-50"
              >
                RECHAZAR
              </button>
              <button 
                onClick={handleAccept}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                ACEPTAR PEDIDO
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}