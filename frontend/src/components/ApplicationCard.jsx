
import { useState } from "react";
import PropTypes from "prop-types";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

const statusVariants = {
  APPLIED: "default",
  INTERVIEW: "secondary",
  OFFER: "outline",
  REJECTED: "destructive",
};

function ApplicationCard({ application }) {
  const [showDetails, setShowDetails] = useState(false);

  const badgeVariant =
    statusVariants[application.status] || "default";

  return (
    <Card className="h-full transition-shadow hover:shadow-md">
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <CardTitle className="truncate text-lg">
              {application.company}
            </CardTitle>

            <p className="mt-1 text-sm text-muted-foreground">
              {application.role}
            </p>
          </div>

          <Badge variant={badgeVariant}>
            {application.status}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <div>
          <p className="text-xs font-medium text-muted-foreground">
            Applied Date
          </p>

          <p className="text-sm">
            {application.applied_date || "Not available"}
          </p>
        </div>

        <Dialog open={showDetails} onOpenChange={setShowDetails}>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setShowDetails(true)}
          >
            Show Details
          </Button>

          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {application.company}
              </DialogTitle>

              <DialogDescription>
                Application details for {application.role}
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4">
              <div>
                <p className="text-xs font-medium text-muted-foreground">
                  Role
                </p>

                <p className="text-sm">
                  {application.role}
                </p>
              </div>

              <div>
                <p className="text-xs font-medium text-muted-foreground">
                  Status
                </p>

                <p className="text-sm">
                  {application.status}
                </p>
              </div>

              <div>
                <p className="text-xs font-medium text-muted-foreground">
                  Applied Date
                </p>

                <p className="text-sm">
                  {application.applied_date || "Not available"}
                </p>
              </div>

              <div>
                <p className="text-xs font-medium text-muted-foreground">
                  Notes
                </p>

                <p className="text-sm leading-relaxed">
                  {application.notes || "No notes available"}
                </p>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {application.optimistic && (
          <p className="text-sm text-muted-foreground">
            Saving...
          </p>
        )}
      </CardContent>
    </Card>
  );
}

ApplicationCard.propTypes = {
  application: PropTypes.shape({
    id: PropTypes.oneOfType([
      PropTypes.string,
      PropTypes.number,
    ]),
    company: PropTypes.string.isRequired,
    role: PropTypes.string.isRequired,
    status: PropTypes.string.isRequired,
    applied_date: PropTypes.string,
    notes: PropTypes.string,
    optimistic: PropTypes.bool,
  }).isRequired,
};

export default ApplicationCard;
