import { redirect } from 'next/navigation';

/**
 * /consultation is no longer an active route.
 * Reception staff should use /registration.
 */
export default function ConsultationRedirectPage() {
    redirect('/registration');
}
