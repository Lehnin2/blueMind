import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'yrbvvkfvmhtjgovziiai.supabase.co'
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlyYnZ2a2Z2bWh0amdvdnppaWFpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDYyMDI5NjEsImV4cCI6MjA2MTc3ODk2MX0.MafN8wVQyXJ-ciwPi5LePbVegNYJr_vtL-v9vk7bTsE'

export const supabase = createClient(supabaseUrl, supabaseKey)