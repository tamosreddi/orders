import { Order } from '../types/order';

// TODO: Replace with Supabase data fetching
// TODO: Implement real-time subscriptions for order updates
// TODO: Add proper error handling and loading states

const customerNames = [
  'James Smith', 'Maria Garcia', 'David Johnson', 'Jennifer Brown', 'Michael Davis',
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

const getRandomDate = (): string => {
  const start = new Date(2024, 4, 1); // May 1, 2024
  const end = new Date(); // Today
  const randomTime = start.getTime() + Math.random() * (end.getTime() - start.getTime());
  return new Date(randomTime).toISOString().split('T')[0]; // Return YYYY-MM-DD format
};

const channels: Order['channel'][] = ['WHATSAPP', 'SMS', 'EMAIL'];
const statuses: Order['status'][] = ['CONFIRMED', 'PENDING'];

export const mockOrders: Order[] = Array.from({ length: 50 }, (_, index) => {
  const customerName = customerNames[index];
  const randomChannel = channels[Math.floor(Math.random() * channels.length)];
  const randomStatus = statuses[Math.floor(Math.random() * statuses.length)];
  const randomProducts = Math.floor(Math.random() * 10) + 1; // 1-10 products
  
  return {
    id: `ORD-${String(index + 1).padStart(4, '0')}`,
    customer: {
      name: customerName,
      avatar: generateAvatar(customerName),
    },
    channel: randomChannel,
    orderDate: getRandomDate(),
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