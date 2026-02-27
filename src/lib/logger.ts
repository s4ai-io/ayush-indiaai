import fs from 'fs';
import path from 'path';

export function logInteractionToTxt(
    typeLabel: string,
    inputStr: string,
    outputStr?: string,
    errorStr?: string
) {
    try {
        // Backend log directory path
        const logDir = path.join(process.cwd(), 'backend', 'logs', 'model_interactions');

        // Ensure directory exists
        if (!fs.existsSync(logDir)) {
            fs.mkdirSync(logDir, { recursive: true });
        }

        // Generate timestamp
        const now = new Date();
        const timestampFile = now.toISOString()
            .replace(/T/, '_')
            .replace(/:/g, '-')
            .replace(/Z/, '')
            .substring(0, 23); // Keep up to ms

        // Sanitize typeLabel for filename
        const safeLabel = typeLabel.replace(/[^a-zA-Z0-9]/g, '');
        const filePath = path.join(logDir, `${timestampFile}_${safeLabel}.txt`);

        let logContent = `${'='.repeat(50)}\n`;
        logContent += `Type: ${typeLabel}\n`;
        logContent += `Timestamp: ${now.toISOString().replace('T', ' ').replace('Z', '')}\n`;
        logContent += `${'='.repeat(50)}\n\n`;

        logContent += `--- INPUT ---\n${inputStr}\n\n`;

        if (outputStr) {
            logContent += `--- OUTPUT ---\n${outputStr}\n\n`;
        }

        if (errorStr) {
            logContent += `--- ERROR ---\n${errorStr}\n\n`;
        }

        fs.writeFileSync(filePath, logContent, 'utf-8');
    } catch (e) {
        console.error('Failed to write interaction log:', e);
    }
}
