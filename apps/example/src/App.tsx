import { SafeAreaView, StyleSheet } from 'react-native';
import Harness from './harness/Harness';

export default function App() {
  return (
    <SafeAreaView style={styles.root}>
      <Harness />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
});
