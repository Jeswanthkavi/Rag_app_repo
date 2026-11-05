import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || 'https://sbkxmevrereobziaubsl.supabase.co';
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNia3htZXZyZXJlb2J6aWF1YnNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTM0OTkzMDgsImV4cCI6MjEwOTA3NTMwOH0.VO1Xg9HImv5YmJHi2uaqonZt-UPK54zEJL-EuVIydzs';

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
  },
});

