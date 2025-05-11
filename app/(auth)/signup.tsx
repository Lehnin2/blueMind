import { useState } from 'react';
import { StyleSheet, Text, View, TextInput, Alert } from 'react-native';
import { router } from 'expo-router';
import { useAuthStore } from '@/services/auth';
import Button from '@/components/Button';
import PageContainer from '@/components/PageContainer';
import Colors from '@/constants/Colors';
import { useColorScheme } from '@/hooks/useColorScheme';

export default function SignupScreen() {
  const colorScheme = useColorScheme();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const signup = useAuthStore((state) => state.signup);

  const handleSignup = async () => {
    if (!name || !email || !password) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    try {
      setLoading(true);
      await signup(email, password, name);
      router.replace('/(tabs)');
    } catch (error) {
      Alert.alert('Error', 'Failed to create account. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageContainer>
      <View style={styles.container}>
        <Text style={[styles.title, { color: Colors[colorScheme].text }]}>
          Create Account
        </Text>
        <Text style={[styles.subtitle, { color: Colors[colorScheme].text }]}>
          Sign up to get started
        </Text>

        <View style={styles.form}>
          <TextInput
            style={[styles.input, { color: Colors[colorScheme].text }]}
            placeholder="Full Name"
            placeholderTextColor={Colors[colorScheme].text}
            value={name}
            onChangeText={setName}
            autoCapitalize="words"
          />
          <TextInput
            style={[styles.input, { color: Colors[colorScheme].text }]}
            placeholder="Email"
            placeholderTextColor={Colors[colorScheme].text}
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
          />
          <TextInput
            style={[styles.input, { color: Colors[colorScheme].text }]}
            placeholder="Password"
            placeholderTextColor={Colors[colorScheme].text}
            value={password}
            onChangeText={setPassword}
            secureTextEntry
          />

          <Button
            title={loading ? 'Creating Account...' : 'Sign Up'}
            onPress={handleSignup}
            disabled={loading}
            style={styles.button}
          />

          <Text
            style={[styles.link, { color: Colors[colorScheme].primary }]}
            onPress={() => router.push('/login')}
          >
            Already have an account? Sign in
          </Text>
        </View>
      </View>
    </PageContainer>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    justifyContent: 'center',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    marginBottom: 32,
  },
  form: {
    width: '100%',
  },
  input: {
    height: 50,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    paddingHorizontal: 16,
    marginBottom: 16,
    fontSize: 16,
  },
  button: {
    marginTop: 16,
  },
  link: {
    textAlign: 'center',
    marginTop: 16,
    fontSize: 16,
  },
}); 