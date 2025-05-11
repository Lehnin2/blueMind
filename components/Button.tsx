import React from 'react';
import {
  StyleSheet,
  Text,
  ActivityIndicator,
  ViewStyle,
  TextStyle,
  TouchableOpacity,
  TouchableOpacityProps,
} from 'react-native';
import Colors from '@/constants/Colors';
import { useColorScheme } from '@/hooks/useColorScheme';

type ButtonProps = {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'text';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  loading?: boolean;
  style?: ViewStyle;
  textStyle?: TextStyle;
  children?: React.ReactNode;
} & TouchableOpacityProps; // you can extend TouchableOpacityProps if you like

const Button = React.forwardRef<
  React.ElementRef<typeof TouchableOpacity>,
  ButtonProps
>(
  (
    {
      title,
      onPress,
      variant = 'primary',
      size = 'medium',
      disabled = false,
      loading = false,
      style,
      textStyle,
      children,
      ...touchableProps
    },
    ref
  ) => {
    const colorScheme = useColorScheme();

    // Determine button and text styles
    const getButtonStyles = (): {
      buttonStyle: ViewStyle;
      textColor: string;
    } => {
      let buttonStyle: ViewStyle = {};
      let textColor = Colors[colorScheme].text;

      // Variant
      switch (variant) {
        case 'primary':
          buttonStyle = { backgroundColor: Colors[colorScheme].primary };
          textColor = '#fff';
          break;
        case 'secondary':
          buttonStyle = { backgroundColor: Colors[colorScheme].secondary };
          textColor = '#fff';
          break;
        case 'outline':
          buttonStyle = {
            backgroundColor: 'transparent',
            borderWidth: 1,
            borderColor: Colors[colorScheme].primary,
          };
          textColor = Colors[colorScheme].primary;
          break;
        case 'text':
          buttonStyle = { backgroundColor: 'transparent' };
          textColor = Colors[colorScheme].primary;
          break;
      }

      // Size
      const paddingMap: Record<string, { v: number; h: number }> = {
        small: { v: 8, h: 16 },
        medium: { v: 12, h: 24 },
        large: { v: 16, h: 32 },
      };
      const { v, h } = paddingMap[size];
      buttonStyle = { ...buttonStyle, paddingVertical: v, paddingHorizontal: h };

      // Disabled/Loading opacity
      if (disabled || loading) {
        buttonStyle = { ...buttonStyle, opacity: 0.5 };
      }

      return { buttonStyle, textColor };
    };

    const { buttonStyle, textColor } = getButtonStyles();

    return (
      <TouchableOpacity
        ref={ref}
        onPress={onPress}
        disabled={disabled || loading}
        style={[styles.button, buttonStyle, style]}
        {...touchableProps}
      >
        {loading ? (
          <ActivityIndicator size="small" color={textColor} />
        ) : (
          <>
            <Text
              style={[
                styles.text,
                {
                  color: textColor,
                  fontSize: size === 'small' ? 14 : size === 'medium' ? 16 : 18,
                },
                textStyle,
              ]}
            >
              {title}
            </Text>
            {children}
          </>
        )}
      </TouchableOpacity>
    );
  }
);

Button.displayName = 'Button';

const styles = StyleSheet.create({
  button: {
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  text: {
    fontFamily: 'Inter-Medium',
    textAlign: 'center',
  },
});

export default Button;
