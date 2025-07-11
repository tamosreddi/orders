import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { OrderStatusBadge } from '../components/OrderStatusBadge'
import { mockOrders } from '../lib/mockOrders'

// Basic component tests as specified in PRP
describe('Orders Dashboard Components', () => {
  test('OrderStatusBadge renders confirmed status correctly', () => {
    render(<OrderStatusBadge status="CONFIRMED" />)
    expect(screen.getByText('Confirmed')).toBeInTheDocument()
  })

  test('OrderStatusBadge renders pending status correctly', () => {
    render(<OrderStatusBadge status="PENDING" />)
    expect(screen.getByText('Pending')).toBeInTheDocument()
  })

  test('mock orders data is generated correctly', () => {
    expect(mockOrders).toHaveLength(50)
    expect(mockOrders[0]).toHaveProperty('id')
    expect(mockOrders[0]).toHaveProperty('customer')
    expect(mockOrders[0]).toHaveProperty('status')
    expect(mockOrders[0].customer).toHaveProperty('name')
    expect(mockOrders[0].customer).toHaveProperty('avatar')
  })

  test('mock orders contain valid status values', () => {
    const statuses = mockOrders.map(order => order.status)
    const validStatuses = ['CONFIRMED', 'PENDING']
    statuses.forEach(status => {
      expect(validStatuses).toContain(status)
    })
  })

  test('mock orders contain valid channel values', () => {
    const channels = mockOrders.map(order => order.channel)
    const validChannels = ['WHATSAPP', 'SMS', 'EMAIL']
    channels.forEach(channel => {
      expect(validChannels).toContain(channel)
    })
  })
})