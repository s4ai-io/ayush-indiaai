import { redirect } from 'next/navigation';

/**
 * /trends is a deprecated static placeholder page.
 * Live disease trend data is available on the public health dashboard.
 */
export default function TrendsRedirectPage() {
    redirect('/public-health/dashboard');
}
