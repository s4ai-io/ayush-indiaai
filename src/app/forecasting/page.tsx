import { redirect } from 'next/navigation';

/**
 * /forecasting is a deprecated static placeholder page.
 * Live public health data is available on the dashboard.
 */
export default function ForecastingRedirectPage() {
    redirect('/public-health/dashboard');
}
