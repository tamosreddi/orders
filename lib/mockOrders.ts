import { Order, OrderDetails, OrderProduct } from '../types/order';

// TODO: Replace with Supabase data fetching
// TODO: Implement real-time subscriptions for order updates
// TODO: Add proper error handling and loading states

const customerNames = [
  'Restaurant One', 'Maria Garcia', 'David Johnson', 'Jennifer Brown', 'Michael Davis',
  'Sarah Wilson', 'Christopher Moore', 'Jessica Taylor', 'Matthew Anderson', 'Ashley Thomas',
  'Joshua Jackson', 'Amanda White', 'Daniel Harris', 'Stephanie Martin', 'Andrew Thompson',
  'Melissa Garcia', 'Kenneth Johnson', 'Deborah Martinez', 'Paul Robinson', 'Sharon Clark',
  'Mark Rodriguez', 'Carol Lewis', 'Steven Lee', 'Ruth Walker', 'Edward Hall',
  'Helen Allen', 'Jason Young', 'Lisa Hernandez', 'Kevin King', 'Nancy Wright',
  'Brian Lopez', 'Betty Hill', 'Ryan Scott', 'Dorothy Green', 'Jacob Adams',
  'Sandra Baker', 'Gary Gonzalez', 'Kimberly Nelson', 'Nicholas Carter', 'Donna Mitchell',
  'Eric Perez', 'Carol Roberts', 'Jonathan Turner', 'Michelle Phillips', 'Stephen Campbell',
  'Emily Parker', 'Larry Evans', 'Donna Edwards', 'Justin Collins', 'Linda Stewart'
];

const generateAvatar = (name: string): string => {
  // Generate consistent avatar URLs based on name
  const seed = name.replace(/\s+/g, '').toLowerCase();
  return `https://api.dicebear.com/7.x/avataaars/svg?seed=${seed}&backgroundColor=b6e3f4,c0aede,d1d4f9`;
};

const generateCustomerCode = (index: number): string => {
  return String(60000 + index * 47 + Math.floor(Math.random() * 100)).substring(0, 5);
};

const getRandomReceivedDate = (): string => {
  const start = new Date(2024, 8, 20); // Sept 20, 2024
  const end = new Date(2024, 8, 26); // Sept 26, 2024
  const randomTime = start.getTime() + Math.random() * (end.getTime() - start.getTime());
  return new Date(randomTime).toISOString().split('T')[0]; // Return YYYY-MM-DD format
};

const getRandomReceivedTime = (): string => {
  const hours = Math.floor(Math.random() * 12) + 8; // 8 AM to 7 PM
  const minutes = Math.floor(Math.random() * 60);
  const period = hours >= 12 ? 'PM' : 'AM';
  const displayHours = hours > 12 ? hours - 12 : hours;
  return `${displayHours}:${minutes.toString().padStart(2, '0')} ${period}`;
};

const getRandomDeliveryDate = (): string => {
  const start = new Date(2025, 9, 1); // Oct 1, 2025
  const end = new Date(2025, 9, 10); // Oct 10, 2025
  const randomTime = start.getTime() + Math.random() * (end.getTime() - start.getTime());
  return new Date(randomTime).toISOString().split('T')[0]; // Return YYYY-MM-DD format
};

const channels: Order['channel'][] = ['WHATSAPP', 'SMS', 'EMAIL'];
const statuses: Order['status'][] = ['CONFIRMED', 'PENDING', 'REVIEW'];

export const mockOrders: Order[] = Array.from({ length: 281 }, (_, index) => {
  const customerName = customerNames[index % customerNames.length];
  const randomChannel = channels[Math.floor(Math.random() * channels.length)];
  const randomStatus = statuses[Math.floor(Math.random() * statuses.length)];
  const randomProducts = Math.floor(Math.random() * 10) + 1; // 1-10 products
  
  return {
    id: `${index + 1}`,
    customer: {
      name: customerName,
      avatar: generateAvatar(customerName),
      code: generateCustomerCode(index),
    },
    channel: randomChannel,
    receivedDate: getRandomReceivedDate(),
    receivedTime: getRandomReceivedTime(),
    deliveryDate: getRandomDeliveryDate(),
    products: randomProducts,
    status: randomStatus,
  };
});

// TODO: Replace with Supabase query
export const getOrders = async (): Promise<Order[]> => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 100));
  return mockOrders;
};

// TODO: Replace with Supabase update
export const updateOrderStatus = async (orderId: string, status: Order['status']): Promise<void> => {
  // Simulate API call
  await new Promise(resolve => setTimeout(resolve, 500));
  const order = mockOrders.find(o => o.id === orderId);
  if (order) {
    order.status = status;
  }
};

// TODO: Replace with Supabase bulk update
export const bulkUpdateOrderStatus = async (orderIds: string[], status: Order['status']): Promise<void> => {
  // Simulate bulk API call
  await new Promise(resolve => setTimeout(resolve, 1000));
  orderIds.forEach(orderId => {
    const order = mockOrders.find(o => o.id === orderId);
    if (order) {
      order.status = status;
    }
  });
};

// Mock detailed order data for review
const mockOrderProducts: OrderProduct[] = [
  {
    id: 'CB101',
    name: 'Frijoles Negros (2 Kg)',
    unit: 'Embalar',
    quantity: 1,
    unitPrice: 4.00,
    linePrice: 4.00
  },
  {
    id: 'EVO102',
    name: 'Aceite de oliva Loazzo (2 l)',
    unit: 'Botella',
    quantity: 1,
    unitPrice: 12.00,
    linePrice: 12.00
  },
  {
    id: 'PP103',
    name: 'La Molisana- Bucatini',
    unit: 'Embalar',
    quantity: 3,
    unitPrice: 5.00,
    linePrice: 15.00
  },
  {
    id: 'OTS104',
    name: 'Tomates Strianese San Marzano DOP',
    unit: 'Poder',
    quantity: 2,
    unitPrice: 6.00,
    linePrice: 12.00
  },
  {
    id: 'GTB105',
    name: 'Té Kusmi (500 g)',
    unit: 'Poder',
    quantity: 2,
    unitPrice: 10.00,
    linePrice: 20.00
  },
  {
    id: 'RSE106',
    name: 'Catena Zapata - Alta Malbec 2018',
    unit: 'Botella',
    quantity: 2,
    unitPrice: 25.00,
    linePrice: 50.00
  },
  {
    id: 'WWB107',
    name: 'Warburtons - Enteros En Rebanadas Medianas',
    unit: 'Embalar',
    quantity: 2,
    unitPrice: 3.00,
    linePrice: 6.00
  },
  {
    id: 'OFA108',
    name: 'Manzanas Fuji (2 Kg)',
    unit: 'Bolsa',
    quantity: 1,
    unitPrice: 8.00,
    linePrice: 8.00
  },
  {
    id: 'EWB107',
    name: 'Olivos - Grasa entera',
    unit: 'Embalar',
    quantity: 1,
    unitPrice: 5.00,
    linePrice: 5.00
  }
];

// TODO: Replace with Supabase query
export const getOrderDetails = async (orderId: string): Promise<OrderDetails | null> => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 100));
  
  // Find base order
  const baseOrder = mockOrders.find(o => o.id === orderId);
  if (!baseOrder) return null;

  // Create detailed order
  const orderDetails: OrderDetails = {
    id: baseOrder.id,
    customer: {
      ...baseOrder.customer,
      address: '123 Main Street, Nueva York, NY 10001'
    },
    channel: baseOrder.channel,
    receivedDate: baseOrder.receivedDate,
    receivedTime: baseOrder.receivedTime,
    deliveryDate: baseOrder.deliveryDate,
    postalCode: '232442',
    products: mockOrderProducts,
    totalAmount: mockOrderProducts.reduce((sum, p) => sum + p.linePrice, 0),
    additionalComment: '',
    attachments: ['captura_whatsapp_26_07.png'],
    whatsappMessage: `Hola,
Disculpa por el pedido tardío
esta semana.
Frijoles 1 paquete
Aceite de oliva 1 botella
Pasta 3 paquetes
Salsa de tomate 2 frascos
Té verde 2
Vino tinto 2 botellas
Pan integral 2 barras
Manzanas orgánicas 1`,
    status: baseOrder.status
  };

  return orderDetails;
};