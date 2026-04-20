/**
 * BookingContext - Manages booking state across the booking wizard steps.
 * Handles search results, selected train, passengers, and payment flow.
 */
import React, { createContext, useContext, useReducer, useCallback } from 'react';

const BookingContext = createContext(null);

const initialState = {
  // Step tracking
  currentStep: 1, // 1: Search, 2: Select Train, 3: Passengers, 4: Review, 5: Payment
  
  // Search parameters
  searchParams: {
    fromStation: null,
    toStation: null,
    journeyDate: '',
    classType: '',
    quota: 'GN',
  },
  
  // Search results
  searchResults: [],
  isSearching: false,
  searchError: null,
  
  // Selected train
  selectedTrain: null,
  selectedClass: null,
  
  // Passengers
  passengers: [],
  contactInfo: {
    email: '',
    phone: '',
  },
  
  // Fare calculation
  fareBreakdown: {
    baseFare: 0,
    reservationCharge: 0,
    superfastCharge: 0,
    gst: 0,
    totalFare: 0,
    farePerPassenger: 0,
  },
  
  // Payment
  paymentMethod: null,
  paymentStatus: null,
  transactionId: null,
  
  // Booking result
  booking: null,
  bookingError: null,
  isBooking: false,
};

const actionTypes = {
  SET_STEP: 'SET_STEP',
  SET_SEARCH_PARAMS: 'SET_SEARCH_PARAMS',
  SET_SEARCHING: 'SET_SEARCHING',
  SET_SEARCH_RESULTS: 'SET_SEARCH_RESULTS',
  SET_SEARCH_ERROR: 'SET_SEARCH_ERROR',
  SELECT_TRAIN: 'SELECT_TRAIN',
  SELECT_CLASS: 'SELECT_CLASS',
  ADD_PASSENGER: 'ADD_PASSENGER',
  UPDATE_PASSENGER: 'UPDATE_PASSENGER',
  REMOVE_PASSENGER: 'REMOVE_PASSENGER',
  SET_CONTACT_INFO: 'SET_CONTACT_INFO',
  SET_FARE_BREAKDOWN: 'SET_FARE_BREAKDOWN',
  SET_PAYMENT_METHOD: 'SET_PAYMENT_METHOD',
  SET_PAYMENT_STATUS: 'SET_PAYMENT_STATUS',
  SET_BOOKING: 'SET_BOOKING',
  SET_BOOKING_ERROR: 'SET_BOOKING_ERROR',
  SET_IS_BOOKING: 'SET_IS_BOOKING',
  RESET_BOOKING: 'RESET_BOOKING',
  RESET_ALL: 'RESET_ALL',
};

function bookingReducer(state, action) {
  switch (action.type) {
    case actionTypes.SET_STEP:
      return { ...state, currentStep: action.payload };

    case actionTypes.SET_SEARCH_PARAMS:
      return {
        ...state,
        searchParams: { ...state.searchParams, ...action.payload },
      };

    case actionTypes.SET_SEARCHING:
      return { ...state, isSearching: action.payload };

    case actionTypes.SET_SEARCH_RESULTS:
      return {
        ...state,
        searchResults: action.payload,
        isSearching: false,
        searchError: null,
      };

    case actionTypes.SET_SEARCH_ERROR:
      return {
        ...state,
        searchError: action.payload,
        isSearching: false,
        searchResults: [],
      };

    case actionTypes.SELECT_TRAIN:
      return { ...state, selectedTrain: action.payload };

    case actionTypes.SELECT_CLASS:
      return { ...state, selectedClass: action.payload };

    case actionTypes.ADD_PASSENGER:
      return {
        ...state,
        passengers: [...state.passengers, action.payload],
      };

    case actionTypes.UPDATE_PASSENGER:
      return {
        ...state,
        passengers: state.passengers.map((p, idx) =>
          idx === action.payload.index ? { ...p, ...action.payload.data } : p
        ),
      };

    case actionTypes.REMOVE_PASSENGER:
      return {
        ...state,
        passengers: state.passengers.filter((_, idx) => idx !== action.payload),
      };

    case actionTypes.SET_CONTACT_INFO:
      return {
        ...state,
        contactInfo: { ...state.contactInfo, ...action.payload },
      };

    case actionTypes.SET_FARE_BREAKDOWN:
      return { ...state, fareBreakdown: action.payload };

    case actionTypes.SET_PAYMENT_METHOD:
      return { ...state, paymentMethod: action.payload };

    case actionTypes.SET_PAYMENT_STATUS:
      return {
        ...state,
        paymentStatus: action.payload.status,
        transactionId: action.payload.transactionId || state.transactionId,
      };

    case actionTypes.SET_BOOKING:
      return {
        ...state,
        booking: action.payload,
        isBooking: false,
        bookingError: null,
      };

    case actionTypes.SET_BOOKING_ERROR:
      return {
        ...state,
        bookingError: action.payload,
        isBooking: false,
      };

    case actionTypes.SET_IS_BOOKING:
      return { ...state, isBooking: action.payload };

    case actionTypes.RESET_BOOKING:
      return {
        ...state,
        selectedTrain: null,
        selectedClass: null,
        passengers: [],
        contactInfo: { email: '', phone: '' },
        fareBreakdown: initialState.fareBreakdown,
        paymentMethod: null,
        paymentStatus: null,
        transactionId: null,
        booking: null,
        bookingError: null,
        currentStep: 1,
      };

    case actionTypes.RESET_ALL:
      return initialState;

    default:
      return state;
  }
}

export function BookingProvider({ children }) {
  const [state, dispatch] = useReducer(bookingReducer, initialState);

  // Step navigation
  const setStep = useCallback((step) => {
    dispatch({ type: actionTypes.SET_STEP, payload: step });
  }, []);

  const nextStep = useCallback(() => {
    dispatch({ type: actionTypes.SET_STEP, payload: state.currentStep + 1 });
  }, [state.currentStep]);

  const prevStep = useCallback(() => {
    dispatch({ type: actionTypes.SET_STEP, payload: Math.max(1, state.currentStep - 1) });
  }, [state.currentStep]);

  // Search actions
  const setSearchParams = useCallback((params) => {
    dispatch({ type: actionTypes.SET_SEARCH_PARAMS, payload: params });
  }, []);

  const setSearching = useCallback((isSearching) => {
    dispatch({ type: actionTypes.SET_SEARCHING, payload: isSearching });
  }, []);

  const setSearchResults = useCallback((results) => {
    dispatch({ type: actionTypes.SET_SEARCH_RESULTS, payload: results });
  }, []);

  const setSearchError = useCallback((error) => {
    dispatch({ type: actionTypes.SET_SEARCH_ERROR, payload: error });
  }, []);

  // Train selection
  const selectTrain = useCallback((train) => {
    dispatch({ type: actionTypes.SELECT_TRAIN, payload: train });
  }, []);

  const selectClass = useCallback((classType) => {
    dispatch({ type: actionTypes.SELECT_CLASS, payload: classType });
  }, []);

  // Passenger actions
  const addPassenger = useCallback((passenger) => {
    const newPassenger = {
      name: '',
      age: '',
      gender: 'Male',
      berthPreference: 'No Preference',
      idType: '',
      idNumber: '',
      ...passenger,
    };
    dispatch({ type: actionTypes.ADD_PASSENGER, payload: newPassenger });
  }, []);

  const updatePassenger = useCallback((index, data) => {
    dispatch({ type: actionTypes.UPDATE_PASSENGER, payload: { index, data } });
  }, []);

  const removePassenger = useCallback((index) => {
    dispatch({ type: actionTypes.REMOVE_PASSENGER, payload: index });
  }, []);

  const setContactInfo = useCallback((info) => {
    dispatch({ type: actionTypes.SET_CONTACT_INFO, payload: info });
  }, []);

  // Fare actions
  const setFareBreakdown = useCallback((breakdown) => {
    dispatch({ type: actionTypes.SET_FARE_BREAKDOWN, payload: breakdown });
  }, []);

  const calculateFare = useCallback(() => {
    if (!state.selectedTrain || !state.selectedClass || state.passengers.length === 0) {
      return;
    }

    // Get fare per km from class (simplified calculation)
    const fareRates = {
      'SL': 0.45,
      '3A': 1.20,
      '2A': 1.80,
      '1A': 2.50,
      'CC': 1.50,
      'EC': 2.80,
      '2S': 0.30,
      'GN': 0.20,
    };

    const distance = state.selectedTrain.Distance || 500; // default 500km
    const ratePerKm = fareRates[state.selectedClass] || 0.45;
    const baseFarePerPerson = Math.round(distance * ratePerKm);
    
    const numPassengers = state.passengers.length;
    const baseFare = baseFarePerPerson * numPassengers;
    const reservationCharge = 40 * numPassengers;
    const superfastCharge = state.selectedTrain.Train_Type?.toLowerCase().includes('superfast') ? 45 * numPassengers : 0;
    const subtotal = baseFare + reservationCharge + superfastCharge;
    const gst = Math.round(subtotal * 0.05);
    const totalFare = subtotal + gst;

    dispatch({
      type: actionTypes.SET_FARE_BREAKDOWN,
      payload: {
        baseFare,
        reservationCharge,
        superfastCharge,
        gst,
        totalFare,
        farePerPassenger: Math.round(totalFare / numPassengers),
        distance,
        numPassengers,
      },
    });
  }, [state.selectedTrain, state.selectedClass, state.passengers]);

  // Payment actions
  const setPaymentMethod = useCallback((method) => {
    dispatch({ type: actionTypes.SET_PAYMENT_METHOD, payload: method });
  }, []);

  const setPaymentStatus = useCallback((status, transactionId) => {
    dispatch({
      type: actionTypes.SET_PAYMENT_STATUS,
      payload: { status, transactionId },
    });
  }, []);

  // Booking actions
  const setBooking = useCallback((booking) => {
    dispatch({ type: actionTypes.SET_BOOKING, payload: booking });
  }, []);

  const setBookingError = useCallback((error) => {
    dispatch({ type: actionTypes.SET_BOOKING_ERROR, payload: error });
  }, []);

  const setIsBooking = useCallback((isBooking) => {
    dispatch({ type: actionTypes.SET_IS_BOOKING, payload: isBooking });
  }, []);

  // Reset actions
  const resetBooking = useCallback(() => {
    dispatch({ type: actionTypes.RESET_BOOKING });
  }, []);

  const resetAll = useCallback(() => {
    dispatch({ type: actionTypes.RESET_ALL });
  }, []);

  // Validation helpers
  const canProceedToStep = useCallback((step) => {
    switch (step) {
      case 2: // Select Train - needs search results
        return state.searchResults.length > 0;
      case 3: // Passengers - needs train and class selected
        return state.selectedTrain && state.selectedClass;
      case 4: // Review - needs at least one passenger
        return state.passengers.length > 0 && state.passengers.every(p => p.name && p.age);
      case 5: // Payment - needs contact info
        return state.contactInfo.email && state.contactInfo.phone;
      default:
        return true;
    }
  }, [state]);

  const value = {
    // State
    ...state,
    
    // Step navigation
    setStep,
    nextStep,
    prevStep,
    
    // Search
    setSearchParams,
    setSearching,
    setSearchResults,
    setSearchError,
    
    // Train selection
    selectTrain,
    selectClass,
    
    // Passengers
    addPassenger,
    updatePassenger,
    removePassenger,
    setContactInfo,
    
    // Fare
    setFareBreakdown,
    calculateFare,
    
    // Payment
    setPaymentMethod,
    setPaymentStatus,
    
    // Booking
    setBooking,
    setBookingError,
    setIsBooking,
    
    // Reset
    resetBooking,
    resetAll,
    
    // Validation
    canProceedToStep,
  };

  return (
    <BookingContext.Provider value={value}>
      {children}
    </BookingContext.Provider>
  );
}

export function useBooking() {
  const context = useContext(BookingContext);
  if (!context) {
    throw new Error('useBooking must be used within a BookingProvider');
  }
  return context;
}

export default BookingContext;
