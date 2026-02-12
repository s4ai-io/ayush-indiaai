
import EHRForm from "@/components/EHR/EHRForm";

export default function EHRPage() {
    return (
        <div className="py-8">
            <div className="mb-8 text-center">
                <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white sm:text-4xl">
                    Electronic Health Record
                </h1>
                <p className="mt-2 text-lg text-gray-600 dark:text-gray-400">
                    Create comprehensive patient records with AI assistance.
                </p>
            </div>
            <EHRForm />
        </div>
    );
}
