const { understory } = require('./understory')

test('construct a Micropub client', () => {
  const endpoint = 'https://alice.example'
  const client = new understory.MicropubClient(endpoint)
  expect(client.endpoint).toBe(endpoint)
})
