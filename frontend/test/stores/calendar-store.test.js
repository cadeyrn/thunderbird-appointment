import {
  expect,
  test,
  beforeEach,
  describe,
  beforeAll,
  afterAll,
  afterEach,
} from 'vitest';
import { useCalendarStore } from '@/stores/calendar-store';
import { createPinia, setActivePinia } from 'pinia';
import { setupServer } from 'msw/node';
import { HttpResponse, http } from 'msw';
import { createFetch } from '@vueuse/core';

const API_URL = 'http://localhost';

const restHandlers = [
  http.get(`${API_URL}/me/calendars`, async () => HttpResponse.json([
    {
      id: 1,
      title: 'title',
      color: '#123456',
      connected: true,
    },
    {
      id: 2,
      title: 'title',
      color: '#123456',
      connected: false,
    },
  ])),
];

const server = setupServer(...restHandlers);
/*server.events.on('request:start', ({ request }) => {
  console.log('Outgoing:', request.method, request.url);
});*/

describe('Calendar Store', () => {
  // Create a pinia instance before each test
  beforeEach(() => {
    setActivePinia(createPinia());
  });
  // Start server before all tests
  beforeAll(() => server.listen());

  // Close server after all tests
  afterAll(() => server.close());

  // Reset handlers after each test `important for test isolation`
  afterEach(() => server.resetHandlers());

  test('init', () => {
    const calStore = useCalendarStore();
    expect(calStore.isLoaded).toBe(false);
    expect(calStore.calendars.length).toBe(0);
  });

  test('fetch', async () => {
    const calStore = useCalendarStore();
    await calStore.fetch(createFetch({ baseUrl: API_URL }));
    expect(calStore.calendars.length).toBe(2);
  });

  test('unconnected', async () => {
    const calStore = useCalendarStore();
    await calStore.fetch(createFetch({ baseUrl: API_URL }));
    expect(calStore.unconnectedCalendars.length).toBe(1);
  });

  test('connected', async () => {
    const calStore = useCalendarStore();
    await calStore.fetch(createFetch({ baseUrl: API_URL }));
    expect(calStore.connectedCalendars.length).toBe(1);
  });

  test('reset', async () => {
    const calStore = useCalendarStore();
    await calStore.fetch(createFetch({ baseUrl: API_URL }));

    // Check if calendars exist
    expect(calStore.isLoaded).toBe(true);
    expect(calStore.calendars.length).toBe(2);

    // Reset the user which should null all user data.
    calStore.$reset();

    // Ensure our data is null/don't exist
    expect(calStore.isLoaded).toBe(false);
    expect(calStore.calendars.length).toBe(0);
  });
});
