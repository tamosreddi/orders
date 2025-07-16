import { Customer, CustomerLabel, CustomerStatus, CustomerInvitationStatus } from '../types/customer';

const customerNames = [
  'Noodle Bar', 'Okuneva Restaurant', 'Ryan and Troy', 'Terrase Dine', 'Tim Dim Sum',
  'Wonton Palace', 'Sakura Sushi', 'Pasta Milano', 'Burger House', 'Taco Libre',
  'Pizza Corner', 'Café Central', 'Bistro 47', 'Golden Dragon', 'Ocean View',
  'Mountain Grill', 'Urban Kitchen', 'Spice Route', 'Fresh Garden', 'Harbor Lights'
];

const customerPersonNames = [
  'John Chen', 'Maria Okuneva', 'Ryan Thompson', 'Sarah Terrase', 'Tim Wong',
  'David Wang', 'Yuki Tanaka', 'Marco Milano', 'Mike Burger', 'Carlos Lopez',
  'Tony Pizza', 'Anna Central', 'Jean Bistro', 'Li Dragon', 'Ocean Smith',
  'Mike Mountain', 'Alex Urban', 'Raj Spice', 'Emma Garden', 'Captain Harbor'
];

const generateAvatar = (name: string): string => {
  const seed = name.replace(/\s+/g, '').toLowerCase();
  return `https://api.dicebear.com/7.x/initials/svg?seed=${seed}&backgroundColor=b6e3f4,c0aede,d1d4f9`;
};

const generateCustomerCode = (index: number): string => {
  return String(60000 + index * 47 + Math.floor(Math.random() * 100)).substring(0, 5);
};

const generateLabels = (): CustomerLabel[] => {
  const labelTypes = [
    { name: 'Dairy', color: '#FEF3C7' },
    { name: 'Carnes', color: '#FEE2E2' },
    { name: 'Restaurant', color: '#E0F2FE' },
    { name: 'Bar', color: '#F3E8FF' }
  ];
  
  // Each customer gets 1-2 labels randomly
  const numLabels = Math.floor(Math.random() * 2) + 1;
  const selectedLabels = labelTypes.sort(() => 0.5 - Math.random()).slice(0, numLabels);
  
  return selectedLabels.map((label, index) => ({
    id: `label-${index}`,
    name: label.name,
    color: label.color,
    value: '10789' // Common value from the image
  }));
};

const getRandomDate = (start: Date, end: Date): string => {
  const date = new Date(start.getTime() + Math.random() * (end.getTime() - start.getTime()));
  return date.toISOString().split('T')[0];
};

const getRandomFutureDate = (): string => {
  const start = new Date();
  const end = new Date(start.getTime() + 30 * 24 * 60 * 60 * 1000); // 30 days from now
  return getRandomDate(start, end);
};

const getRandomPastDate = (): string => {
  const end = new Date();
  const start = new Date(end.getTime() - 60 * 24 * 60 * 60 * 1000); // 60 days ago
  return getRandomDate(start, end);
};

const statuses: CustomerStatus[] = ['ORDERING', 'AT_RISK', 'STOPPED_ORDERING', 'NO_ORDERS_YET'];
const invitationStatuses: CustomerInvitationStatus[] = ['ACTIVE', 'PENDING'];

export const mockCustomers: Customer[] = Array.from({ length: 20 }, (_, index) => {
  const customerName = customerNames[index % customerNames.length];
  const customerPersonName = customerPersonNames[index % customerPersonNames.length];
  const status = statuses[Math.floor(Math.random() * statuses.length)];
  const invitationStatus = invitationStatuses[Math.floor(Math.random() * invitationStatuses.length)];
  
  // Generate realistic data based on status
  let lastOrdered: string | null = null;
  let expectedOrder: string | null = null;
  let totalOrders = 0;
  let totalSpent = 0;
  
  if (status === 'ORDERING') {
    lastOrdered = getRandomPastDate();
    expectedOrder = getRandomFutureDate();
    totalOrders = Math.floor(Math.random() * 50) + 10;
    totalSpent = totalOrders * (Math.random() * 200 + 50);
  } else if (status === 'AT_RISK') {
    lastOrdered = getRandomPastDate();
    expectedOrder = getRandomFutureDate();
    totalOrders = Math.floor(Math.random() * 30) + 5;
    totalSpent = totalOrders * (Math.random() * 150 + 40);
  } else if (status === 'STOPPED_ORDERING') {
    lastOrdered = getRandomPastDate();
    expectedOrder = null;
    totalOrders = Math.floor(Math.random() * 20) + 1;
    totalSpent = totalOrders * (Math.random() * 100 + 30);
  } else {
    lastOrdered = null;
    expectedOrder = null;
    totalOrders = 0;
    totalSpent = 0;
  }
  
  return {
    id: `${index + 1}`,
    name: customerName,
    customerName: customerPersonName,
    avatar: generateAvatar(customerName),
    code: generateCustomerCode(index),
    labels: generateLabels(),
    lastOrdered,
    expectedOrder,
    status,
    invitationStatus,
    email: `${customerName.toLowerCase().replace(/\s+/g, '')}@email.com`,
    phone: `+1${Math.floor(Math.random() * 9000000000) + 1000000000}`,
    address: `${Math.floor(Math.random() * 999) + 1} Main St, City, State`,
    joinedDate: getRandomPastDate(),
    totalOrders,
    totalSpent: Math.round(totalSpent * 100) / 100
  };
});

// TODO: Replace with Supabase data fetching
export const getCustomers = async (): Promise<Customer[]> => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 100));
  return mockCustomers;
};

// TODO: Replace with Supabase query
export const getCustomerById = async (customerId: string): Promise<Customer | null> => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 100));
  return mockCustomers.find(c => c.id === customerId) || null;
};

// TODO: Replace with Supabase query
export const getCustomerByCode = async (customerCode: string): Promise<Customer | null> => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 100));
  return mockCustomers.find(c => c.code === customerCode) || null;
};

// TODO: Replace with Supabase update
export const updateCustomer = async (customerId: string, updates: Partial<Customer>): Promise<void> => {
  // Simulate API call
  await new Promise(resolve => setTimeout(resolve, 500));
  const customer = mockCustomers.find(c => c.id === customerId);
  if (customer) {
    Object.assign(customer, updates);
  }
};

export interface CreateCustomerData {
  customerName: string;
  businessName: string;
  businessLocation: string;
  phone: string;
  email: string;
  preferredContact: 'phone' | 'email';
  customerCode: string;
  avatar: string;
  labels: CustomerLabel[];
}

// TODO: Replace with Supabase insert
export const createCustomer = async (customerData: CreateCustomerData, shouldSendInvite: boolean = true): Promise<Customer> => {
  // Simulate API call
  await new Promise(resolve => setTimeout(resolve, 800));
  
  const newCustomer: Customer = {
    id: String(mockCustomers.length + 1),
    name: customerData.businessName,
    customerName: customerData.customerName,
    avatar: customerData.avatar || generateAvatar(customerData.businessName),
    code: customerData.customerCode,
    labels: customerData.labels,
    lastOrdered: null,
    expectedOrder: null,
    status: 'NO_ORDERS_YET',
    invitationStatus: shouldSendInvite ? 'PENDING' : 'ACTIVE',
    email: customerData.email,
    phone: customerData.phone,
    address: customerData.businessLocation,
    joinedDate: new Date().toISOString().split('T')[0],
    totalOrders: 0,
    totalSpent: 0
  };
  
  // Add to mock data
  mockCustomers.push(newCustomer);
  
  return newCustomer;
};