export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  public: {
    Tables: {
      distributors: {
        Row: {
          id: string
          business_name: string
          domain: string | null
          subdomain: string | null
          api_key_hash: string | null
          webhook_secret: string | null
          subscription_tier: 'FREE' | 'BASIC' | 'PREMIUM' | 'ENTERPRISE'
          subscription_status: 'ACTIVE' | 'SUSPENDED' | 'CANCELLED'
          billing_email: string | null
          contact_name: string | null
          contact_email: string
          contact_phone: string | null
          address: string | null
          timezone: string
          locale: string
          currency: string
          ai_enabled: boolean
          ai_model_preference: string
          ai_confidence_threshold: number
          monthly_ai_budget_usd: number
          status: 'ACTIVE' | 'INACTIVE' | 'PENDING_SETUP'
          onboarding_completed: boolean
          max_customers: number | null
          max_monthly_messages: number | null
          max_monthly_ai_requests: number | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          business_name: string
          domain?: string | null
          subdomain?: string | null
          api_key_hash?: string | null
          webhook_secret?: string | null
          subscription_tier?: 'FREE' | 'BASIC' | 'PREMIUM' | 'ENTERPRISE'
          subscription_status?: 'ACTIVE' | 'SUSPENDED' | 'CANCELLED'
          billing_email?: string | null
          contact_name?: string | null
          contact_email: string
          contact_phone?: string | null
          address?: string | null
          timezone?: string
          locale?: string
          currency?: string
          ai_enabled?: boolean
          ai_model_preference?: string
          ai_confidence_threshold?: number
          monthly_ai_budget_usd?: number
          status?: 'ACTIVE' | 'INACTIVE' | 'PENDING_SETUP'
          onboarding_completed?: boolean
          max_customers?: number | null
          max_monthly_messages?: number | null
          max_monthly_ai_requests?: number | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          business_name?: string
          domain?: string | null
          subdomain?: string | null
          api_key_hash?: string | null
          webhook_secret?: string | null
          subscription_tier?: 'FREE' | 'BASIC' | 'PREMIUM' | 'ENTERPRISE'
          subscription_status?: 'ACTIVE' | 'SUSPENDED' | 'CANCELLED'
          billing_email?: string | null
          contact_name?: string | null
          contact_email?: string
          contact_phone?: string | null
          address?: string | null
          timezone?: string
          locale?: string
          currency?: string
          ai_enabled?: boolean
          ai_model_preference?: string
          ai_confidence_threshold?: number
          monthly_ai_budget_usd?: number
          status?: 'ACTIVE' | 'INACTIVE' | 'PENDING_SETUP'
          onboarding_completed?: boolean
          max_customers?: number | null
          max_monthly_messages?: number | null
          max_monthly_ai_requests?: number | null
          created_at?: string
          updated_at?: string
        }
        Relationships: []
      }
      customers: {
        Row: {
          id: string
          distributor_id: string
          business_name: string
          contact_person_name: string | null
          customer_code: string
          email: string | null
          phone: string | null
          address: string | null
          avatar_url: string | null
          status: 'ORDERING' | 'AT_RISK' | 'STOPPED_ORDERING' | 'NO_ORDERS_YET'
          invitation_status: 'ACTIVE' | 'PENDING'
          joined_date: string | null
          last_ordered_date: string | null
          expected_order_date: string | null
          total_orders: number
          total_spent: number
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          distributor_id: string
          business_name: string
          contact_person_name?: string | null
          customer_code: string
          email: string | null
          phone?: string | null
          address?: string | null
          avatar_url?: string | null
          status?: 'ORDERING' | 'AT_RISK' | 'STOPPED_ORDERING' | 'NO_ORDERS_YET'
          invitation_status?: 'ACTIVE' | 'PENDING'
          joined_date?: string | null
          last_ordered_date?: string | null
          expected_order_date?: string | null
          total_orders?: number
          total_spent?: number
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          distributor_id?: string
          business_name?: string
          contact_person_name?: string | null
          customer_code?: string
          email?: string | null
          phone?: string | null
          address?: string | null
          avatar_url?: string | null
          status?: 'ORDERING' | 'AT_RISK' | 'STOPPED_ORDERING' | 'NO_ORDERS_YET'
          invitation_status?: 'ACTIVE' | 'PENDING'
          joined_date?: string | null
          last_ordered_date?: string | null
          expected_order_date?: string | null
          total_orders?: number
          total_spent?: number
          created_at?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "customers_distributor_id_fkey"
            columns: ["distributor_id"]
            isOneToOne: false
            referencedRelation: "distributors"
            referencedColumns: ["id"]
          }
        ]
      }
      customer_labels: {
        Row: {
          id: string
          distributor_id: string
          name: string
          color: string
          description: string | null
          is_predefined: boolean
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          distributor_id: string
          name: string
          color: string
          description?: string | null
          is_predefined?: boolean
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          distributor_id?: string
          name?: string
          color?: string
          description?: string | null
          is_predefined?: boolean
          created_at?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "customer_labels_distributor_id_fkey"
            columns: ["distributor_id"]
            isOneToOne: false
            referencedRelation: "distributors"
            referencedColumns: ["id"]
          }
        ]
      }
      customer_label_assignments: {
        Row: {
          customer_id: string
          label_id: string
          value: string | null
          assigned_at: string
        }
        Insert: {
          customer_id: string
          label_id: string
          value?: string | null
          assigned_at?: string
        }
        Update: {
          customer_id?: string
          label_id?: string
          value?: string | null
          assigned_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "customer_label_assignments_customer_id_fkey"
            columns: ["customer_id"]
            isOneToOne: false
            referencedRelation: "customers"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "customer_label_assignments_label_id_fkey"
            columns: ["label_id"]
            isOneToOne: false
            referencedRelation: "customer_labels"
            referencedColumns: ["id"]
          }
        ]
      }
      conversations: {
        Row: {
          id: string
          customer_id: string
          distributor_id: string
          channel: 'WHATSAPP' | 'SMS' | 'EMAIL'
          status: 'ACTIVE' | 'ARCHIVED' | 'CLOSED'
          last_message_at: string
          last_message_id: string | null
          unread_count: number
          ai_context_summary: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          customer_id: string
          distributor_id: string
          channel: 'WHATSAPP' | 'SMS' | 'EMAIL'
          status?: 'ACTIVE' | 'ARCHIVED' | 'CLOSED'
          last_message_at?: string
          last_message_id?: string | null
          unread_count?: number
          ai_context_summary?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          customer_id?: string
          distributor_id?: string
          channel?: 'WHATSAPP' | 'SMS' | 'EMAIL'
          status?: 'ACTIVE' | 'ARCHIVED' | 'CLOSED'
          last_message_at?: string
          last_message_id?: string | null
          unread_count?: number
          ai_context_summary?: string | null
          created_at?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "conversations_customer_id_fkey"
            columns: ["customer_id"]
            isOneToOne: false
            referencedRelation: "customers"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "conversations_distributor_id_fkey"
            columns: ["distributor_id"]
            isOneToOne: false
            referencedRelation: "distributors"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "conversations_last_message_fkey"
            columns: ["last_message_id"]
            isOneToOne: false
            referencedRelation: "messages"
            referencedColumns: ["id"]
          }
        ]
      }
      messages: {
        Row: {
          id: string
          conversation_id: string
          content: string
          is_from_customer: boolean
          message_type: 'TEXT' | 'IMAGE' | 'AUDIO' | 'FILE' | 'ORDER_CONTEXT'
          status: 'SENT' | 'DELIVERED' | 'READ' | 'FAILED' | 'RECEIVED'
          attachments: Json[]
          ai_processed: boolean
          ai_confidence: number | null
          ai_extracted_intent: string | null
          ai_extracted_products: Json | null
          ai_suggested_responses: Json | null
          external_message_id: string | null
          order_context_id: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          conversation_id: string
          content: string
          is_from_customer?: boolean
          message_type?: 'TEXT' | 'IMAGE' | 'AUDIO' | 'FILE' | 'ORDER_CONTEXT'
          status?: 'SENT' | 'DELIVERED' | 'READ' | 'FAILED' | 'RECEIVED'
          attachments?: Json[]
          ai_processed?: boolean
          ai_confidence?: number | null
          ai_extracted_intent?: string | null
          ai_extracted_products?: Json | null
          ai_suggested_responses?: Json | null
          external_message_id?: string | null
          order_context_id?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          conversation_id?: string
          content?: string
          is_from_customer?: boolean
          message_type?: 'TEXT' | 'IMAGE' | 'AUDIO' | 'FILE' | 'ORDER_CONTEXT'
          status?: 'SENT' | 'DELIVERED' | 'READ' | 'FAILED' | 'RECEIVED'
          attachments?: Json[]
          ai_processed?: boolean
          ai_confidence?: number | null
          ai_extracted_intent?: string | null
          ai_extracted_products?: Json | null
          ai_suggested_responses?: Json | null
          external_message_id?: string | null
          order_context_id?: string | null
          created_at?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "messages_conversation_id_fkey"
            columns: ["conversation_id"]
            isOneToOne: false
            referencedRelation: "conversations"
            referencedColumns: ["id"]
          }
        ]
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}