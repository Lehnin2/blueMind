import { StyleSheet, Text, View, ViewStyle, TouchableOpacity } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Colors from '@/constants/Colors';
import { useColorScheme } from '@/hooks/useColorScheme';
import { Filter, MapPin, Bell, Settings, Menu } from 'lucide-react-native';

type HeaderBarProps = {
  title: string;
  subtitle?: string;
  rightContent?: React.ReactNode;
  rightAction?: {
    icon: string;
    onPress: () => void;
  };
  style?: ViewStyle;
};

export default function HeaderBar({ title, subtitle, rightContent, rightAction, style }: HeaderBarProps) {
  const colorScheme = useColorScheme();
  const insets = useSafeAreaInsets();
  
  // Function to render the appropriate icon based on the icon name
  const renderIcon = (iconName: string, color: string) => {
    const iconProps = { size: 24, color, strokeWidth: 2 };
    
    switch (iconName) {
      case 'filter':
        return <Filter {...iconProps} />;
      case 'map-pin':
        return <MapPin {...iconProps} />;
      case 'bell':
        return <Bell {...iconProps} />;
      case 'settings':
        return <Settings {...iconProps} />;
      case 'menu':
        return <Menu {...iconProps} />;
      default:
        return <Filter {...iconProps} />;
    }
  };
  
  return (
    <View 
      style={[
        styles.container, 
        { 
          paddingTop: Math.max(insets.top, 16),
          backgroundColor: Colors[colorScheme].background 
        },
        style
      ]}
    >
      <View style={styles.titleContainer}>
        <Text style={[styles.title, { color: Colors[colorScheme].text }]}>
          {title}
        </Text>
        {subtitle && (
          <Text style={[styles.subtitle, { color: 'rgba(255, 255, 255, 0.7)' }]}>
            {subtitle}
          </Text>
        )}
      </View>
      {rightContent && (
        <View style={styles.rightContent}>
          {rightContent}
        </View>
      )}
      {rightAction && (
        <TouchableOpacity 
          style={styles.actionButton}
          onPress={rightAction.onPress}
        >
          {renderIcon(rightAction.icon, Colors[colorScheme].text)}
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  titleContainer: {
    flex: 1,
  },
  title: {
    fontSize: 28,
    fontFamily: 'Inter-Bold',
  },
  subtitle: {
    fontSize: 16,
    marginTop: 4,
    fontFamily: 'Inter-Regular',
  },
  rightContent: {
    marginLeft: 16,
  },
  actionButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 16,
  },
});