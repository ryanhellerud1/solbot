import {
  Box,
  Flex,
  Text,
  Button,
  Container,
  Heading,
  Badge,
  Grid,
  GridItem
} from '@chakra-ui/react'
import { useState, useEffect } from 'react'
import axios from 'axios'

const API_URL = 'http://localhost:8000'

interface BotStatus {
  is_running: boolean
  network: string
  wallet_balance: number
  tokens_scanned: number
  active_trades: number
}

interface TokenData {
  address: string
  symbol: string
  price: number
  volume_24h: number
  price_change_1h: number
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <Box p={5} shadow="md" borderWidth="1px" borderRadius="lg" bg="white">
      <Text fontSize="sm" color="gray.500">
        {label}
      </Text>
      <Text fontSize="2xl" fontWeight="bold">
        {value}
      </Text>
    </Box>
  )
}

function App() {
  const [status, setStatus] = useState<BotStatus | null>(null)
  const [tokens, setTokens] = useState<TokenData[]>([])
  const [notification, setNotification] = useState<{
    message: string
    type: 'success' | 'error'
  } | null>(null)

  const showNotification = (message: string, type: 'success' | 'error') => {
    setNotification({ message, type })
    setTimeout(() => setNotification(null), 3000)
  }

  const fetchStatus = async () => {
    try {
      const response = await axios.get(`${API_URL}/status`)
      setStatus(response.data)
    } catch (error) {
      console.error('Error fetching status:', error)
    }
  }

  const fetchTokens = async () => {
    try {
      const response = await axios.get(`${API_URL}/tokens`)
      setTokens(response.data)
    } catch (error) {
      console.error('Error fetching tokens:', error)
    }
  }

  const handleStartBot = async () => {
    try {
      await axios.post(`${API_URL}/start`)
      showNotification('Bot Started Successfully', 'success')
      fetchStatus()
    } catch (error) {
      showNotification('Error Starting Bot', 'error')
    }
  }

  const handleStopBot = async () => {
    try {
      await axios.post(`${API_URL}/stop`)
      showNotification('Bot Stopped Successfully', 'success')
      fetchStatus()
    } catch (error) {
      showNotification('Error Stopping Bot', 'error')
    }
  }

  useEffect(() => {
    fetchStatus()
    fetchTokens()
    const interval = setInterval(() => {
      fetchStatus()
      fetchTokens()
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <Box minH="100vh" bg="gray.50" py={8}>
      <Container maxW="container.xl">
        {notification && (
          <Box 
            mb={4} 
            p={4} 
            borderRadius="md" 
            bg={notification.type === 'success' ? 'green.100' : 'red.100'}
            color={notification.type === 'success' ? 'green.800' : 'red.800'}
          >
            {notification.message}
          </Box>
        )}
        
        <Flex direction="column" gap={8}>
          {/* Header */}
          <Flex justify="space-between" align="center">
            <Heading size="lg">Solana Trading Bot</Heading>
            <Badge
              colorScheme={status?.is_running ? 'green' : 'red'}
              p={2}
              borderRadius="md"
            >
              {status?.is_running ? 'Running' : 'Stopped'}
            </Badge>
          </Flex>

          {/* Stats */}
          <Grid templateColumns={{ base: '1fr', md: 'repeat(4, 1fr)' }} gap={4}>
            <GridItem>
              <StatCard
                label="Network"
                value={status?.network || '-'}
              />
            </GridItem>
            <GridItem>
              <StatCard
                label="Wallet Balance"
                value={`${status?.wallet_balance?.toFixed(4) || '-'} SOL`}
              />
            </GridItem>
            <GridItem>
              <StatCard
                label="Tokens Scanned"
                value={status?.tokens_scanned || 0}
              />
            </GridItem>
            <GridItem>
              <StatCard
                label="Active Trades"
                value={status?.active_trades || 0}
              />
            </GridItem>
          </Grid>

          {/* Controls */}
          <Flex gap={4}>
            <Button
              colorScheme="green"
              onClick={handleStartBot}
              disabled={status?.is_running}
            >
              Start Bot
            </Button>
            <Button
              colorScheme="red"
              onClick={handleStopBot}
              disabled={!status?.is_running}
            >
              Stop Bot
            </Button>
          </Flex>

          {/* Token Table */}
          <Box bg="white" p={6} borderRadius="lg" shadow="sm">
            <Heading size="md" mb={4}>Recent Tokens</Heading>
            <Box overflowX="auto">
              <Box as="table" w="full" style={{ borderCollapse: 'collapse' }}>
                <Box as="thead">
                  <Box as="tr">
                    <Box as="th" p={2} textAlign="left">Symbol</Box>
                    <Box as="th" p={2} textAlign="left">Address</Box>
                    <Box as="th" p={2} textAlign="right">Price</Box>
                    <Box as="th" p={2} textAlign="right">24h Volume</Box>
                    <Box as="th" p={2} textAlign="right">1h Change</Box>
                  </Box>
                </Box>
                <Box as="tbody">
                  {tokens.map((token) => (
                    <Box as="tr" key={token.address} borderTopWidth="1px" borderColor="gray.200">
                      <Box as="td" p={2}>{token.symbol}</Box>
                      <Box as="td" p={2}>
                        <Text maxW="200px" overflow="hidden" textOverflow="ellipsis" whiteSpace="nowrap">
                          {token.address}
                        </Text>
                      </Box>
                      <Box as="td" p={2} textAlign="right">${token.price.toFixed(4)}</Box>
                      <Box as="td" p={2} textAlign="right">${token.volume_24h.toLocaleString()}</Box>
                      <Box as="td" p={2} textAlign="right">
                        <Text
                          color={token.price_change_1h >= 0 ? 'green.500' : 'red.500'}
                        >
                          {token.price_change_1h.toFixed(2)}%
                        </Text>
                      </Box>
                    </Box>
                  ))}
                </Box>
              </Box>
            </Box>
          </Box>
        </Flex>
      </Container>
    </Box>
  )
}

export default App
