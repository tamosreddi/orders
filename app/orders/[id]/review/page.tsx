'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Image from 'next/image';
import { X } from 'lucide-react';
import { OrderDetails, OrderProduct } from '../../../../types/order';
import { Customer } from '../../../../types/customer';
import { getOrderById, updateOrderProduct, addOrderProduct, deleteOrderProduct, updateOrderDeliveryDate, updateOrderStatus, OrderError } from '../../../../lib/api/orders';
import { getCustomerByCode } from '../../../../lib/api/customers';
import { EditableProductsTable } from '../../../../components/OrderReview/EditableProductsTable';
import { ClickableCustomerDisplay } from '../../../../components/OrderReview/ClickableCustomerDisplay';
import { CustomerDetailsPanel } from '../../../../components/customer_components/CustomerDetailsPanel';
import { DatePicker } from '../../../../components/ui/DatePicker';

export default function OrderReviewPage() {
  const params = useParams();
  const router = useRouter();
  const orderId = params.id as string;
  
  const [orderDetails, setOrderDetails] = useState<OrderDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [products, setProducts] = useState<OrderProduct[]>([]);
  const [comment, setComment] = useState('');
  const [deliveryDate, setDeliveryDate] = useState<Date | null>(null);
  
  // Customer details panel state
  const [isCustomerPanelOpen, setIsCustomerPanelOpen] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [customerLoading, setCustomerLoading] = useState(false);

  useEffect(() => {
    const loadOrderDetails = async () => {
      try {
        const details = await getOrderById(orderId);
        if (details) {
          setOrderDetails(details);
          setProducts(details.products);
          setComment(details.additionalComment);
          
          // Parse delivery date
          if (details.deliveryDate && details.deliveryDate !== 'por confirmar') {
            try {
              setDeliveryDate(new Date(details.deliveryDate));
            } catch (error) {
              console.warn('Invalid delivery date format:', details.deliveryDate);
              setDeliveryDate(null);
            }
          } else {
            setDeliveryDate(null);
          }
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

  const handleProductsChange = async (updatedProducts: OrderProduct[]) => {
    setProducts(updatedProducts);
  };
  
  const handleUpdateProduct = async (productId: string, updates: Partial<any>) => {
    try {
      console.log('🐛 DEBUG: handleUpdateProduct called with:', {
        productId,
        updates,
        updateKeys: Object.keys(updates)
      });
      
      const dbUpdates: Partial<{product_name: string; product_unit: string; quantity: number; unit_price: number; line_price: number}> = {};
      if ('name' in updates) dbUpdates.product_name = updates.name!;
      if ('unit' in updates) dbUpdates.product_unit = updates.unit!;
      if ('quantity' in updates) dbUpdates.quantity = updates.quantity!;
      
      // FIX: Handle both camelCase and snake_case for unit_price
      if ('unitPrice' in updates) dbUpdates.unit_price = updates.unitPrice!;
      if ('unit_price' in updates) dbUpdates.unit_price = updates.unit_price!;
      
      if ('linePrice' in updates) dbUpdates.line_price = updates.linePrice!;
      if ('line_price' in updates) dbUpdates.line_price = updates.line_price!;
      
      console.log('🔄 Mapped to dbUpdates:', dbUpdates);
      
      await updateOrderProduct(productId, dbUpdates);
    } catch (error) {
      console.error('Error updating product:', error);
      throw error;
    }
  };
  
  const handleAddProduct = async (productData: Omit<OrderProduct, 'id'>) => {
    try {
      const dbProduct = {
        product_name: productData.name,
        product_unit: productData.unit,
        quantity: productData.quantity,
        unit_price: productData.unitPrice,
        line_price: productData.linePrice
      };
      
      const newProduct = await addOrderProduct(orderId, dbProduct);
      return newProduct;
    } catch (error) {
      console.error('Error adding product:', error);
      throw error;
    }
  };
  
  const handleDeleteProduct = async (productId: string) => {
    try {
      await deleteOrderProduct(productId);
    } catch (error) {
      console.error('Error deleting product:', error);
      throw error;
    }
  };
  
  const handleDeliveryDateChange = async (date: Date | null) => {
    setDeliveryDate(date);
    
    if (date && orderDetails) {
      try {
        const formattedDate = date.toISOString().split('T')[0]; // YYYY-MM-DD format for database
        await updateOrderDeliveryDate(orderDetails.id, formattedDate);
        
        // Update local state
        setOrderDetails({
          ...orderDetails,
          deliveryDate: formattedDate
        });
      } catch (error) {
        console.error('Error updating delivery date:', error);
        // Revert on error
        setDeliveryDate(orderDetails.deliveryDate !== 'por confirmar' ? new Date(orderDetails.deliveryDate) : null);
      }
    } else if (!date && orderDetails) {
      try {
        await updateOrderDeliveryDate(orderDetails.id, 'por confirmar');
        
        // Update local state
        setOrderDetails({
          ...orderDetails,
          deliveryDate: 'por confirmar'
        });
      } catch (error) {
        console.error('Error updating delivery date:', error);
        // Revert on error
        setDeliveryDate(orderDetails.deliveryDate !== 'por confirmar' ? new Date(orderDetails.deliveryDate) : null);
      }
    }
  };

  const handleAccept = async () => {
    try {
      // Update order status to CONFIRMED (accepted)
      await updateOrderStatus(orderId, 'CONFIRMED');
      
      console.log('Order accepted successfully:', orderId);
      
      // Redirect to orders page
      router.push('/orders');
    } catch (error) {
      console.error('Error accepting order:', error);
      // TODO: Show error notification to user
    }
  };

  const handleReject = () => {
    // TODO: Implement order rejection
    console.log('Rejecting order');
    router.push('/orders');
  };

  const handleCustomerClick = async () => {
    if (!orderDetails) return;
    
    setCustomerLoading(true);
    try {
      const customer = await getCustomerByCode(orderDetails.customer.code);
      if (customer) {
        setSelectedCustomer(customer);
        setIsCustomerPanelOpen(true);
      }
    } catch (error) {
      console.error('Error loading customer details:', error);
    } finally {
      setCustomerLoading(false);
    }
  };

  const handleCustomerPanelClose = () => {
    setIsCustomerPanelOpen(false);
    setSelectedCustomer(null);
  };

  const handleCustomerUpdate = (updatedCustomer: Customer) => {
    setSelectedCustomer(updatedCustomer);
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
      <div className="bg-white border-b border-gray-200 px-6 py-2">
        <div className="flex items-center justify-end">
          <div className="flex items-center space-x-4">
            <button 
              onClick={handleClose}
              className="text-reddi-navyblue text-sm hover:text-reddi-navyblue/70"
            >
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
        <div className="w-2/5 bg-white border-r border-gray-200 flex flex-col">
          {/* WhatsApp Header - Fixed */}
          <div className="bg-teal-600 text-white p-3 flex items-center space-x-3 flex-shrink-0">
            <Image 
              src={orderDetails.customer.avatar} 
              alt={orderDetails.customer.name}
              width={32}
              height={32}
              className="rounded-full object-cover"
            />
            <div>
              <div className="font-medium">{orderDetails.customer.name}</div>
              <div className="text-xs opacity-75">
                {new Date(orderDetails.receivedDate).toLocaleDateString('es-ES', { 
                  weekday: 'short', 
                  day: 'numeric', 
                  month: 'short' 
                })}
              </div>
            </div>
          </div>
          
          {/* Chat Messages - Scrollable */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
            {/* Original Message */}
            {orderDetails.originalMessage ? (
              <div className="bg-white rounded-lg p-3 max-w-xs">
                <p className="text-sm whitespace-pre-line">
                  {orderDetails.originalMessage.content}
                </p>
                <div className="text-xs text-gray-500 mt-2">
                  {new Date(orderDetails.originalMessage.timestamp).toLocaleTimeString('es-ES', {
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg p-3 max-w-xs">
                <p className="text-sm whitespace-pre-line">
                  {orderDetails.whatsappMessage}
                </p>
                <div className="text-xs text-gray-500 mt-2">{orderDetails.receivedTime}</div>
              </div>
            )}
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
                    <button className="text-reddi-navyblue hover:text-reddi-navyblue/70 ml-auto">
                      Descargar
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Side - Order Details */}
        <div className="w-3/5 bg-white overflow-y-auto">
          {/* Review Notice */}
          <div className="bg-gray-100 border-b border-gray-200 shadow-sm">
            <div className="p-2 flex items-start space-x-2">
              <div className="w-5 h-3 text-gray-600 mt-0">
                ℹ️
              </div>
              <p className="text-sm text-gray-700">
                Revise todos los elementos: los resultados de la IA no siempre son precisos.
              </p>
            </div>
          </div>

          {/* Top Section - Now scrollable */}
          <div className="p-4">

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
                <div className="text-sm text-reddi-navyblue">{orderDetails.channel}</div>
              </div>
            </div>

            {/* Customer Info and Delivery Date */}
            <div className="grid grid-cols-2 gap-6 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-2">
                  Cliente
                </label>
                <ClickableCustomerDisplay
                  customerName={orderDetails.customer.name}
                  customerCode={orderDetails.customer.code}
                  customerAddress={orderDetails.customer.address}
                  onClick={handleCustomerClick}
                  loading={customerLoading}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-2">
                  Fecha de entrega
                </label>
                <div className="max-w-xs">
                  <DatePicker
                    selected={deliveryDate}
                    onChange={handleDeliveryDateChange}
                    placeholderText="por confirmar"
                    className="w-full"
                    dateFormat="dd/MM/yyyy"
                  />
                </div>
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

          {/* Products Table */}
          <div className="px-4 mb-4">
            <EditableProductsTable 
              products={products} 
              onProductsChange={handleProductsChange}
              onUpdateProduct={handleUpdateProduct}
              onAddProduct={handleAddProduct}
              onDeleteProduct={handleDeleteProduct}
            />
          </div>

          {/* Comment Section */}
          <div className="px-4 mb-4">
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
          <div className="px-4 pb-6">
            <div className="flex justify-end space-x-4">
              <button 
                onClick={handleReject}
                className="px-6 py-2 border border-red-300 text-red-700 rounded-md hover:bg-red-50"
              >
                RECHAZAR
              </button>
              <button 
                onClick={handleAccept}
                className="px-6 py-2 bg-reddi-navyblue text-white rounded-md hover:bg-reddi-navyblue/80"
              >
                ACEPTAR PEDIDO
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Customer Details Panel */}
      <CustomerDetailsPanel
        customer={selectedCustomer}
        isOpen={isCustomerPanelOpen}
        onClose={handleCustomerPanelClose}
        onCustomerUpdate={handleCustomerUpdate}
      />
    </div>
  );
}